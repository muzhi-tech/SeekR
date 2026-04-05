"""SeekR Evolution CLI — orchestrates the full evolution cycle.

Usage:
    python evolve_cli.py evolve          # Full cycle: collect → detect → generate strategies
    python evolve_cli.py parity          # Run parity audit only
    python evolve_cli.py report          # Generate evolution report
    python evolve_cli.py status          # Show current system health
    python evolve_cli.py status --json   # Machine-readable status
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup — make sibling scripts and seekr.scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parents[1]  # seekr/
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_PROJECT_ROOT))

from effect_collector import (  # noqa: E402
    DegradationDetector,
    MetricAggregator,
    MetricReader,
    ReportGenerator,
)
from seekr.scripts.models import (  # noqa: E402
    ABTestConfig,
    DegradationAlert,
    EvolutionReport,
    Strategy,
    now_iso,
)

# Lazy imports for strategy_generator / parity_auditor to avoid heavy init
# when those commands are not requested.
strategy_generator_mod = None
parity_auditor_mod = None


def _get_strategy_generator():
    global strategy_generator_mod
    if strategy_generator_mod is None:
        import strategy_generator as _sg
        strategy_generator_mod = _sg
    return strategy_generator_mod


def _get_parity_auditor():
    global parity_auditor_mod
    if parity_auditor_mod is None:
        import parity_auditor as _pa
        parity_auditor_mod = _pa
    return parity_auditor_mod


# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------
METRICS_DIR = str(_SCRIPTS_DIR.parent / "evolution-metrics")
REPORTS_DIR = str(_PROJECT_ROOT / "reports")
SEEKR_DIR = str(_PROJECT_ROOT / "seekr")


# ===================================================================
# Commands
# ===================================================================

def cmd_evolve(args: argparse.Namespace) -> Dict[str, Any]:
    """Full evolution cycle: collect → detect → generate strategies."""
    print("Starting SeekR Evolution Cycle ...\n")

    # 1. Collect metrics
    reader = MetricReader()
    metrics = reader.load_metrics(METRICS_DIR)
    recent = reader.filter_by_time_window(metrics, hours=24)
    print(f"[1/4] Collected {len(recent)} executions (last 24h), {len(metrics)} total")

    if not metrics:
        print("No metrics data available. Aborting evolution cycle.")
        return {"status": "no_data", "timestamp": now_iso()}

    # 2. Pattern recognition — degradation detection
    detector = DegradationDetector()
    alerts = detector.detect_degradation(metrics)
    threshold_alerts = detector.check_sheep_thresholds(recent)
    print(f"[2/4] Pattern recognition: {len(alerts)} degradation alerts, {len(threshold_alerts)} threshold alerts")

    # 3. Trend analysis
    aggregator = MetricAggregator()
    trend_info = aggregator.trend_detection(metrics)
    sheep_trends: Dict[str, Dict[str, Any]] = {}
    dim_stats = aggregator.aggregate_by_dimension(recent)
    for dim in dim_stats:
        dim_scores = [m.sheep_scores.get(dim, 0.0) for m in metrics]
        short_ma = aggregator.moving_average(dim_scores, 7)
        long_ma = aggregator.moving_average(dim_scores, 30)
        s = short_ma[-1] if short_ma else dim_stats[dim]["mean"]
        l = long_ma[-1] if long_ma else dim_stats[dim]["mean"]
        change = ((s - l) / l * 100) if l else 0.0
        # Compute slope (simple linear regression on last N points)
        recent_scores = dim_scores[-7:] if len(dim_scores) >= 7 else dim_scores
        slope = 0.0
        if len(recent_scores) >= 2:
            n = len(recent_scores)
            x_mean = (n - 1) / 2.0
            y_mean = sum(recent_scores) / n
            num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(recent_scores))
            den = sum((i - x_mean) ** 2 for i in range(n))
            slope = num / den if den else 0.0
        # Avg error_count for this dimension (use 0 since errors are per-execution, not per-dim)
        dim_error_count = sum(m.error_count for m in recent) / max(len(recent), 1)
        direction = "declining" if change < -5 else ("improving" if change > 3 else "stable")
        sheep_trends[dim] = {
            "direction": direction,
            "slope": round(slope, 3),
            "error_count": round(dim_error_count, 2),
            "short_ma": round(s, 2),
            "long_ma": round(l, 2),
            "change_pct": round(change, 2),
        }
    print(f"[3/4] Trend: {trend_info.get('trend', 'stable')} ({trend_info.get('change_pct', 0):+.1f}%)")

    # 4. Strategy generation
    sg_mod = _get_strategy_generator()
    gen = sg_mod.StrategyGenerator(degradation_alerts=alerts, sheep_trends=sheep_trends)
    strategies = gen.generate()
    print(f"[4/4] Generated {len(strategies)} strategies")

    # Build result
    report_gen = ReportGenerator()
    report = report_gen.generate_summary(recent, time_window="24h")
    report["degradation_alerts"] = [
        {"skill": a.skill, "dimension": a.dimension, "z_score": a.z_score,
         "severity": a.severity, "trend": a.trend}
        for a in alerts
    ]
    report["proposed_strategies"] = [
        {"strategy_id": s.strategy_id, "type": s.strategy_type,
         "target": s.target_skill, "expected_boost": s.expected_gem_boost,
         "status": s.status}
        for s in strategies
    ]

    # Write report
    _write_report(report, "evolve")

    print(f"\nEvolution cycle complete. Report saved to {REPORTS_DIR}/")
    return report


def cmd_parity(args: argparse.Namespace) -> Dict[str, Any]:
    """Run parity audit."""
    pa_mod = _get_parity_auditor()
    baseline = getattr(args, "baseline", None) or str(_SCRIPTS_DIR.parent / "reference")
    candidate = getattr(args, "candidate", None) or SEEKR_DIR

    print(f"Running parity audit ...\n  Baseline: {baseline}\n  Candidate: {candidate}\n")

    auditor = pa_mod.ParityAuditor(new_version_path=candidate, baseline_path=baseline)
    report = auditor.audit()

    passed = report.passed
    checks_summary = [
        {"name": c.name, "passed": c.passed, "message": c.message}
        for c in report.checks
    ]

    print(f"\nParity Audit Result: {'PASS' if passed else 'FAIL'}")
    for c in checks_summary:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['name']}: {c['message']}")

    if report.blockers:
        print(f"\nBlockers ({len(report.blockers)}):")
        for b in report.blockers:
            print(f"  - {b}")

    result = {
        "timestamp": now_iso(),
        "version": report.version,
        "baseline": report.baseline,
        "passed": passed,
        "checks": checks_summary,
        "blockers": report.blockers,
    }

    _write_report(result, "parity")
    return result


def cmd_report(args: argparse.Namespace) -> Dict[str, Any]:
    """Generate evolution report."""
    window = getattr(args, "window", "24h")
    hours_map = {"24h": 24, "7d": 168, "30d": 720}
    hours = hours_map.get(window, 24)

    reader = MetricReader()
    metrics = reader.load_metrics(METRICS_DIR)
    filtered = reader.filter_by_time_window(metrics, hours=hours)

    if not filtered:
        print(f"No metrics data found for window '{window}'.")
        return {"status": "no_data", "window": window}

    generator = ReportGenerator()
    report = generator.generate_summary(filtered, time_window=window)

    print(generator.format_report(report))
    _write_report(report, f"report-{window}")

    return report


def cmd_status(args: argparse.Namespace) -> Dict[str, Any]:
    """Show current system health summary."""
    reader = MetricReader()
    metrics = reader.load_metrics(METRICS_DIR)
    recent = reader.filter_by_time_window(metrics, hours=24)

    aggregator = MetricAggregator()
    gem_stats = aggregator.aggregate_gem(recent)
    dim_stats = aggregator.aggregate_by_dimension(recent)

    detector = DegradationDetector()
    alerts = detector.detect_degradation(metrics)
    threshold_alerts = detector.check_sheep_thresholds(recent)

    trend = aggregator.trend_detection(metrics)

    status: Dict[str, Any] = {
        "timestamp": now_iso(),
        "total_metrics": len(metrics),
        "last_24h": len(recent),
        "gem": gem_stats,
        "dimensions": {
            dim: {"mean": stats["mean"], "status": _dim_status(stats["mean"], dim)}
            for dim, stats in dim_stats.items()
        },
        "degradation_alerts": len(alerts),
        "threshold_alerts": len(threshold_alerts),
        "trend": trend.get("trend", "unknown"),
    }

    if getattr(args, "json", False):
        print(json.dumps(status, indent=2))
    else:
        print("=" * 45)
        print("  SeekR System Health")
        print("=" * 45)
        print(f"  Timestamp:    {status['timestamp'][:19]}")
        print(f"  Total metrics: {status['total_metrics']}")
        print(f"  Last 24h:      {status['last_24h']}")
        print(f"  GEM:           {gem_stats.get('mean', 0):.1f}")
        print(f"  Trend:         {status['trend']}")
        print(f"  Deg. alerts:   {len(alerts)}")
        print(f"  Thresh. alerts: {len(threshold_alerts)}")
        print()
        print(f"  {'Dim':<4} {'Mean':>6} {'Status':<8}")
        print("  " + "-" * 22)
        for dim, info in status["dimensions"].items():
            print(f"  {dim:<4} {info['mean']:>6.1f} {info['status']:<8}")
        print("=" * 45)

    return status


# ===================================================================
# Helpers
# ===================================================================

def _dim_status(score: float, dim: str) -> str:
    """Quick status for a dimension score."""
    from seekr.scripts.models import CRITICAL_THRESHOLD, WARNING_THRESHOLD, sheep_status
    return sheep_status(score, dim)


def _write_report(data: Dict[str, Any], prefix: str) -> Path:
    """Write a JSON report file to the reports directory."""
    reports_dir = Path(REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)

    ts = now_iso().replace(":", "-").replace("+", "_")[:22]
    filename = f"{prefix}_{ts}.json"
    filepath = reports_dir / filename

    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return filepath


# ===================================================================
# CLI parser
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evolve_cli",
        description="SeekR Evolution Engine CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # evolve
    sub.add_parser("evolve", help="Run full evolution cycle")

    # parity
    parity_p = sub.add_parser("parity", help="Run parity audit")
    parity_p.add_argument("--baseline", help="Path to baseline directory")
    parity_p.add_argument("--candidate", help="Path to candidate (new version) directory")

    # report
    report_p = sub.add_parser("report", help="Generate evolution report")
    report_p.add_argument("--window", default="24h", choices=["24h", "7d", "30d"],
                          help="Time window for the report (default: 24h)")

    # status
    status_p = sub.add_parser("status", help="Show current system health")
    status_p.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "evolve": cmd_evolve,
        "parity": cmd_parity,
        "report": cmd_report,
        "status": cmd_status,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
