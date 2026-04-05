"""SeekR Effect Collector — reads execution metrics, detects degradation, generates reports.

Consumes JSON metric files from evolution-metrics/ and produces EvolutionReport-compatible
summaries with SHEEP/GEM analysis, trend detection, and degradation alerts.
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Ensure seekr.scripts.models is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # seekr/
sys.path.insert(0, str(_PROJECT_ROOT))

from seekr.scripts.models import (  # noqa: E402
    CRITICAL_THRESHOLD,
    DIMENSIONS,
    DIMENSION_WEIGHTS,
    WARNING_THRESHOLD,
    DegradationAlert,
    EvolutionReport,
    ExecutionMetric,
    calculate_gem,
    gem_band,
    now_iso,
    sheep_status,
    z_score,
)

# ---------------------------------------------------------------------------
# Metric file I/O helpers
# ---------------------------------------------------------------------------

# Map the verbose keys used in JSON files (e.g. "S_semantic_coverage") to short
# dimension codes ("S").  The models use short codes internally.
_VERBOSE_KEY_MAP: Dict[str, str] = {
    "S_semantic_coverage": "S",
    "H_human_credibility": "H",
    "E1_evidence_structuring": "E1",
    "E2_ecosystem_integration": "E2",
    "P_performance_monitoring": "P",
}


def _parse_sheep_scores(raw: Any) -> Dict[str, float]:
    """Normalise sheep_scores from JSON into {S: float, H: float, ...}.

    Accepts both formats:
      - {S: 72, H: 65, ...}                (short keys, simple values)
      - {S_semantic_coverage: {raw: 72, weight: 0.25}, ...}  (verbose keys)
    """
    result: Dict[str, float] = {}
    if not isinstance(raw, dict):
        return result

    for key, value in raw.items():
        short_key = _VERBOSE_KEY_MAP.get(key, key)
        if short_key not in DIMENSION_WEIGHTS:
            continue
        if isinstance(value, (int, float)):
            result[short_key] = float(value)
        elif isinstance(value, dict) and "raw" in value:
            result[short_key] = float(value["raw"])
    return result


def _parse_findings_count(raw: Any) -> int:
    """Normalise findings_count: sum if dict, passthrough if int."""
    if isinstance(raw, int):
        return raw
    if isinstance(raw, dict):
        return sum(v for v in raw.values() if isinstance(v, (int, float)))
    return 0


def _json_to_metric(data: Dict[str, Any]) -> ExecutionMetric:
    """Convert a raw JSON dict to an ExecutionMetric dataclass."""
    sheep = _parse_sheep_scores(data.get("sheep_scores", {}))
    gem = data.get("gem_score")
    if gem is None:
        gem = calculate_gem(sheep)

    return ExecutionMetric(
        execution_id=data.get("execution_id", ""),
        timestamp=data.get("timestamp", ""),
        workflow=data.get("workflow", ""),
        skill_name=data.get("skill_name", ""),
        skill_version=data.get("skill_version", ""),
        sheep_scores=sheep,
        gem_score=float(gem),
        findings_count=_parse_findings_count(data.get("findings_count", 0)),
        duration_ms=data.get("duration_ms", 0),
        error_count=data.get("error_count", 0),
    )


# ===================================================================
# MetricReader — load and filter execution metrics
# ===================================================================

class MetricReader:
    """Reads ExecutionMetric JSON files and provides filtering helpers."""

    @staticmethod
    def load_metrics(directory: str) -> List[ExecutionMetric]:
        """Load all .json files from *directory* and return ExecutionMetric list."""
        metrics: List[ExecutionMetric] = []
        dir_path = Path(directory)
        if not dir_path.is_dir():
            return metrics

        for fp in sorted(dir_path.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                metrics.append(_json_to_metric(data))
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                print(f"[WARN] Skipping {fp.name}: {exc}", file=sys.stderr)
        return metrics

    @staticmethod
    def filter_by_skill(metrics: List[ExecutionMetric], skill_name: str) -> List[ExecutionMetric]:
        return [m for m in metrics if m.skill_name == skill_name]

    @staticmethod
    def filter_by_time_window(metrics: List[ExecutionMetric], hours: int) -> List[ExecutionMetric]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result: List[ExecutionMetric] = []
        for m in metrics:
            try:
                ts = datetime.fromisoformat(m.timestamp)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    result.append(m)
            except (ValueError, TypeError):
                continue
        return result

    @staticmethod
    def filter_by_workflow(metrics: List[ExecutionMetric], workflow: str) -> List[ExecutionMetric]:
        return [m for m in metrics if m.workflow == workflow]


# ===================================================================
# MetricAggregator — statistical aggregation
# ===================================================================

class MetricAggregator:
    """Compute statistics over lists of ExecutionMetric."""

    @staticmethod
    def _desc(values: List[float]) -> Dict[str, Any]:
        """Return mean, std, min, max, count for a list of floats."""
        n = len(values)
        if n == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0}
        avg = mean(values)
        sd = stdev(values) if n >= 2 else 0.0
        return {
            "mean": round(avg, 2),
            "std": round(sd, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "count": n,
        }

    def aggregate_gem(self, metrics: List[ExecutionMetric]) -> Dict[str, Any]:
        """Mean, std, min, max, count of gem_score."""
        return self._desc([m.gem_score for m in metrics])

    def aggregate_by_dimension(self, metrics: List[ExecutionMetric]) -> Dict[str, Dict[str, Any]]:
        """Per-dimension stats."""
        buckets: Dict[str, List[float]] = {dim: [] for dim in DIMENSION_WEIGHTS}
        for m in metrics:
            for dim, score in m.sheep_scores.items():
                if dim in buckets:
                    buckets[dim].append(score)
        return {dim: self._desc(scores) for dim, scores in buckets.items()}

    @staticmethod
    def moving_average(scores: List[float], window_size: int) -> List[float]:
        """Simple rolling average. Returns fewer elements than input by (window_size - 1)."""
        if window_size <= 0 or len(scores) < window_size:
            return []
        result: List[float] = []
        for i in range(len(scores) - window_size + 1):
            window = scores[i : i + window_size]
            result.append(round(mean(window), 2))
        return result

    def trend_detection(
        self,
        metrics: List[ExecutionMetric],
        short_window: int = 7,
        long_window: int = 30,
    ) -> Dict[str, Any]:
        """Compare short vs long moving averages for GEM score.

        Returns dict with ``trend`` (declining / improving / stable) and the MA values.
        """
        scores = [m.gem_score for m in metrics]
        short_ma = self.moving_average(scores, short_window)
        long_ma = self.moving_average(scores, long_window)

        result: Dict[str, Any] = {
            "short_ma": short_ma,
            "long_ma": long_ma,
            "trend": "stable",
        }

        if not short_ma or not long_ma:
            return result

        current_short = short_ma[-1]
        current_long = long_ma[-1]

        if current_long == 0:
            return result

        change_pct = ((current_short - current_long) / current_long) * 100
        if change_pct < -10:
            result["trend"] = "declining"
        elif change_pct > 5:
            result["trend"] = "improving"
        else:
            result["trend"] = "stable"

        result["change_pct"] = round(change_pct, 2)
        result["current_short_ma"] = current_short
        result["current_long_ma"] = current_long
        return result


# ===================================================================
# DegradationDetector — z-score based anomaly detection
# ===================================================================

class DegradationDetector:
    """Detect performance degradation using z-score analysis."""

    # Use the first 70% of data as baseline, last 30% as current window
    _SPLIT = 0.7

    def detect_degradation(
        self,
        metrics: List[ExecutionMetric],
        dimension: Optional[str] = None,
    ) -> List[DegradationAlert]:
        """Detect degradation via z-score. If *dimension* is None, check all dimensions + GEM."""
        if len(metrics) < 5:
            return []

        # Sort by timestamp to ensure chronological order
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        split_idx = max(1, int(len(sorted_metrics) * self._SPLIT))
        historical = sorted_metrics[:split_idx]
        current = sorted_metrics[split_idx:]

        if not current:
            return []

        alerts: List[DegradationAlert] = []
        dimensions_to_check = [dimension] if dimension else list(DIMENSION_WEIGHTS.keys()) + ["GEM"]

        # Determine skill name (use most common)
        skill_name = max(set(m.skill_name for m in metrics), key=lambda s: sum(1 for m in metrics if m.skill_name == s))

        for dim in dimensions_to_check:
            if dim == "GEM":
                hist_scores = [m.gem_score for m in historical]
                cur_scores = [m.gem_score for m in current]
            else:
                hist_scores = [m.sheep_scores.get(dim, 0.0) for m in historical]
                cur_scores = [m.sheep_scores.get(dim, 0.0) for m in current]

            if not hist_scores or not cur_scores:
                continue

            hist_mean = mean(hist_scores)
            hist_std = stdev(hist_scores) if len(hist_scores) >= 2 else 0.0
            cur_avg = mean(cur_scores)

            z = z_score(cur_avg, hist_mean, hist_std)

            severity: Optional[str] = None
            if z < -3.0:
                severity = "critical"
            elif z < -2.0:
                severity = "warning"

            if severity:
                # Determine trend
                if len(cur_scores) >= 3:
                    first_half = mean(cur_scores[: len(cur_scores) // 2])
                    second_half = mean(cur_scores[len(cur_scores) // 2 :])
                    if second_half < first_half - 2:
                        trend = "declining"
                    elif second_half > first_half + 2:
                        trend = "improving"
                    else:
                        trend = "flat"
                else:
                    trend = "declining"

                alerts.append(DegradationAlert(
                    skill=skill_name,
                    dimension=dim,
                    z_score=round(z, 3),
                    severity=severity,  # type: ignore[arg-type]
                    trend=trend,
                ))

        return alerts

    @staticmethod
    def check_sheep_thresholds(metrics: List[ExecutionMetric]) -> List[Dict[str, Any]]:
        """Check each SHEEP dimension against CRITICAL/WARNING thresholds.

        Returns a list of dicts with dimension, score, status details.
        """
        if not metrics:
            return []

        results: List[Dict[str, Any]] = []
        # Use latest metric's scores
        latest = max(metrics, key=lambda m: m.timestamp)

        for dim in DIMENSION_WEIGHTS:
            score = latest.sheep_scores.get(dim, 0.0)
            status = sheep_status(score, dim)
            if status != "OK":
                results.append({
                    "dimension": dim,
                    "dimension_name": DIMENSIONS.get(dim, dim),
                    "current_score": score,
                    "status": status,
                    "critical_threshold": CRITICAL_THRESHOLD[dim],
                    "warning_threshold": WARNING_THRESHOLD[dim],
                })

        # Also check GEM
        gem = latest.gem_score
        band = gem_band(gem)
        if band in ("D", "F"):
            results.append({
                "dimension": "GEM",
                "dimension_name": "Overall GEM Score",
                "current_score": gem,
                "status": "CRITICAL" if band == "F" else "WARNING",
                "critical_threshold": 40,
                "warning_threshold": 55,
            })

        return results


# ===================================================================
# ReportGenerator — produce EvolutionReport-compatible output
# ===================================================================

class ReportGenerator:
    """Generate EvolutionReport-compatible summaries."""

    def __init__(self) -> None:
        self.reader = MetricReader()
        self.aggregator = MetricAggregator()
        self.detector = DegradationDetector()

    def generate_summary(
        self,
        metrics: List[ExecutionMetric],
        time_window: str = "24h",
    ) -> Dict[str, Any]:
        """Produce a full summary dict matching EvolutionReport schema.

        Args:
            metrics: List of ExecutionMetric records.
            time_window: Human-readable window label, e.g. "24h", "7d", "30d".

        Returns:
            Dict matching the EvolutionReport schema with additional computed fields.
        """
        if not metrics:
            return {
                "timestamp": now_iso(),
                "window": time_window,
                "total_executions": 0,
                "message": "No metrics data available for the specified window.",
            }

        # --- SHEEP dimension trends ---
        dim_stats = self.aggregator.aggregate_by_dimension(metrics)
        gem_stats = self.aggregator.aggregate_gem(metrics)
        trend_info = self.aggregator.trend_detection(metrics)

        # Build per-dimension trend table
        sheep_trends: Dict[str, str] = {}
        dim_table: List[Dict[str, Any]] = []
        for dim in DIMENSION_WEIGHTS:
            stats = dim_stats.get(dim, {})
            current = stats.get("mean", 0.0)
            status = sheep_status(current, dim)
            short_ma = self.aggregator.moving_average(
                [m.sheep_scores.get(dim, 0.0) for m in metrics], 7
            )
            long_ma = self.aggregator.moving_average(
                [m.sheep_scores.get(dim, 0.0) for m in metrics], 30
            )
            short_avg = short_ma[-1] if short_ma else current
            long_avg = long_ma[-1] if long_ma else current
            change_pct = round(((short_avg - long_avg) / long_avg) * 100, 1) if long_avg else 0.0

            dim_table.append({
                "dim": dim,
                "current": round(current, 1),
                "7d_avg": round(short_avg, 1),
                "30d_avg": round(long_avg, 1),
                "change_pct": change_pct,
                "status": status,
            })

            if change_pct < -5:
                sheep_trends[dim] = "declining"
            elif change_pct > 3:
                sheep_trends[dim] = "improving"
            else:
                sheep_trends[dim] = "stable"

        # --- Degradation alerts ---
        degradation_alerts = self.detector.detect_degradation(metrics)
        threshold_alerts = self.detector.check_sheep_thresholds(metrics)

        # --- Assemble report ---
        report: Dict[str, Any] = {
            "timestamp": now_iso(),
            "window": time_window,
            "total_executions": len(metrics),
            "gem_summary": gem_stats,
            "gem_band": gem_band(gem_stats.get("mean", 0.0)),
            "trend": trend_info.get("trend", "stable"),
            "trend_change_pct": trend_info.get("change_pct", 0.0),
            "sheep_trends": sheep_trends,
            "dimension_table": dim_table,
            "degradation_alerts": [
                {
                    "skill": a.skill,
                    "dimension": a.dimension,
                    "z_score": a.z_score,
                    "severity": a.severity,
                    "trend": a.trend,
                }
                for a in degradation_alerts
            ],
            "threshold_alerts": threshold_alerts,
            "active_tests": [],       # populated by A/B Test Controller
            "proposed_strategies": [], # populated by Strategy Generator
            "parity_summary": None,   # populated by Parity Auditor
        }

        return report

    @staticmethod
    def format_report(report: Dict[str, Any]) -> str:
        """Format a report dict into a human-readable string matching the SKILL.md template."""
        lines: List[str] = []
        ts = report.get("timestamp", "N/A")
        window = report.get("window", "N/A")
        total = report.get("total_executions", 0)

        lines.append("=" * 55)
        lines.append("  SeekR Evolution Report")
        lines.append(f"  Window: {window} | Date: {ts[:10]}")
        lines.append("=" * 55)

        if total == 0:
            lines.append(report.get("message", "No data available."))
            return "\n".join(lines)

        gem_info = report.get("gem_summary", {})
        gem_mean = gem_info.get("mean", 0.0)
        gem_band_val = report.get("gem_band", "?")
        trend = report.get("trend", "stable")
        change = report.get("trend_change_pct", 0.0)

        lines.append(f"\nGEM: {gem_mean} | Band: {gem_band_val} | Trend: {trend} ({change:+.1f}%)")
        lines.append(f"Total executions: {total}\n")

        # Dimension table
        lines.append("## SHEEP Score Trends")
        lines.append("")
        lines.append(f"{'Dim':<4} {'Current':>8} {'7d Avg':>8} {'30d Avg':>8} {'Change':>8} {'Status':<8}")
        lines.append("-" * 50)
        for row in report.get("dimension_table", []):
            lines.append(
                f"{row['dim']:<4} {row['current']:>8.1f} {row['7d_avg']:>8.1f} "
                f"{row['30d_avg']:>8.1f} {row['change_pct']:>+7.1f}% {row['status']:<8}"
            )
        lines.append(
            f"{'GEM':<4} {gem_mean:>8.1f} {'':>8} {'':>8} {change:>+7.1f}% {gem_band_val:<8}"
        )

        # Degradation alerts
        alerts = report.get("degradation_alerts", [])
        threshold_alerts = report.get("threshold_alerts", [])
        lines.append(f"\n## Degradation Alerts ({len(alerts)})")
        if alerts:
            for a in alerts:
                lines.append(f"  [{a['severity'].upper()}] {a['skill']} / {a['dimension']}: z={a['z_score']:.3f} ({a['trend']})")
        else:
            lines.append("  None")

        if threshold_alerts:
            lines.append(f"\n## Threshold Alerts ({len(threshold_alerts)})")
            for ta in threshold_alerts:
                lines.append(
                    f"  [{ta['status']}] {ta['dimension']} ({ta['dimension_name']}): "
                    f"{ta['current_score']:.1f} < {ta['warning_threshold']}"
                )

        lines.append(f"\n## Active A/B Tests: {len(report.get('active_tests', []))}")
        lines.append(f"## Proposed Strategies: {len(report.get('proposed_strategies', []))}")
        parity = report.get("parity_summary")
        if parity:
            lines.append(f"## Parity: {parity}")
        else:
            lines.append("## Parity Audit: pending")

        return "\n".join(lines)


# ===================================================================
# Sample data generator (for testing / demo)
# ===================================================================

def _generate_sample_data(directory: str, count: int = 50) -> None:
    """Create sample JSON metric files for testing."""
    import random

    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    base_time = datetime.now(timezone.utc) - timedelta(hours=count)
    workflows = ["WORKFLOW_A", "WORKFLOW_B", "WORKFLOW_C", "WORKFLOW_D"]
    skills = ["seo-audit", "geo-content", "schema-markup", "on-page-seo"]

    for i in range(count):
        ts = base_time + timedelta(hours=i)
        # Simulate slight degradation over time for testing
        degrade = i * 0.15
        sheep = {
            "S": max(30, min(100, random.gauss(75 - degrade * 0.3, 8))),
            "H": max(30, min(100, random.gauss(70 - degrade * 0.2, 10))),
            "E1": max(30, min(100, random.gauss(68 - degrade * 0.5, 9))),
            "E2": max(30, min(100, random.gauss(72 - degrade * 0.1, 7))),
            "P": max(30, min(100, random.gauss(76 - degrade * 0.15, 6))),
        }
        sheep_rounded = {k: round(v, 1) for k, v in sheep.items()}
        gem = calculate_gem(sheep_rounded)

        record = {
            "execution_id": f"exec-{i:04d}",
            "timestamp": ts.isoformat(),
            "workflow": random.choice(workflows),
            "skill_name": random.choice(skills),
            "skill_version": "1.2.0",
            "sheep_scores": sheep_rounded,
            "gem_score": round(gem, 2),
            "findings_count": random.randint(0, 15),
            "duration_ms": random.randint(5000, 60000),
            "error_count": random.choices([0, 0, 0, 0, 1, 2], k=1)[0],
        }

        fp = dir_path / f"{record['execution_id']}.json"
        fp.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print(f"Generated {count} sample metric files in {directory}")


# ===================================================================
# CLI entry point
# ===================================================================

def main() -> None:
    metrics_dir = str(Path(__file__).resolve().parents[1] / "evolution-metrics")

    # Generate sample data if directory is empty or missing
    if not Path(metrics_dir).is_dir() or not list(Path(metrics_dir).glob("*.json")):
        print(f"No metrics found. Generating sample data in {metrics_dir} ...")
        _generate_sample_data(metrics_dir, count=50)

    # Load and analyse
    reader = MetricReader()
    metrics = reader.load_metrics(metrics_dir)
    print(f"Loaded {len(metrics)} metric records from {metrics_dir}")

    if not metrics:
        print("No data to analyse.")
        return

    # Filter to last 24h
    recent = reader.filter_by_time_window(metrics, hours=24)
    print(f"Last 24h: {len(recent)} records")

    # Generate report
    generator = ReportGenerator()
    report = generator.generate_summary(recent, time_window="24h")
    print()
    print(generator.format_report(report))


if __name__ == "__main__":
    main()
