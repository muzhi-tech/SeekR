"""Unit tests for seekr-evolve/scripts/effect_collector.py."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_EVOLVE_SCRIPTS = str(Path(__file__).resolve().parent.parent / "seekr-evolve" / "scripts")
if _EVOLVE_SCRIPTS not in sys.path:
    sys.path.insert(0, _EVOLVE_SCRIPTS)

from seekr.scripts.models import DegradationAlert, ExecutionMetric, calculate_gem

from effect_collector import (
    DegradationDetector,
    MetricAggregator,
    MetricReader,
    ReportGenerator,
    _json_to_metric,
    _parse_findings_count,
    _parse_sheep_scores,
)


def _make_metric(**overrides) -> dict:
    """Create a minimal metric JSON dict with defaults."""
    base = {
        "execution_id": "test-exec-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow": "WORKFLOW_A",
        "skill_name": "test-skill",
        "skill_version": "1.0.0",
        "sheep_scores": {"S": 75, "H": 65, "E1": 60, "E2": 55, "P": 70},
        "gem_score": 65.5,
        "findings_count": 5,
        "duration_ms": 3000,
        "error_count": 0,
    }
    base.update(overrides)
    return base


class TestParseSheepScores(unittest.TestCase):
    def test_short_keys(self):
        raw = {"S": 75, "H": 65, "E1": 60, "E2": 55, "P": 70}
        result = _parse_sheep_scores(raw)
        self.assertEqual(result, {"S": 75.0, "H": 65.0, "E1": 60.0, "E2": 55.0, "P": 70.0})

    def test_verbose_keys(self):
        raw = {
            "S_semantic_coverage": {"raw": 80, "weight": 0.25},
            "H_human_credibility": {"raw": 70, "weight": 0.25},
        }
        result = _parse_sheep_scores(raw)
        self.assertEqual(result, {"S": 80.0, "H": 70.0})

    def test_mixed_keys(self):
        raw = {"S": 75, "H_human_credibility": {"raw": 60, "weight": 0.25}}
        result = _parse_sheep_scores(raw)
        self.assertEqual(result, {"S": 75.0, "H": 60.0})

    def test_empty(self):
        self.assertEqual(_parse_sheep_scores({}), {})
        self.assertEqual(_parse_sheep_scores(None), {})
        self.assertEqual(_parse_sheep_scores("bad"), {})

    def test_unknown_keys_ignored(self):
        raw = {"S": 75, "X": 99}
        result = _parse_sheep_scores(raw)
        self.assertNotIn("X", result)


class TestParseFindingsCount(unittest.TestCase):
    def test_int(self):
        self.assertEqual(_parse_findings_count(5), 5)

    def test_dict(self):
        self.assertEqual(_parse_findings_count({"critical": 2, "high": 3}), 5)

    def test_other(self):
        self.assertEqual(_parse_findings_count("bad"), 0)
        self.assertEqual(_parse_findings_count(None), 0)


class TestJsonToMetric(unittest.TestCase):
    def test_basic_conversion(self):
        data = _make_metric()
        metric = _json_to_metric(data)
        self.assertIsInstance(metric, ExecutionMetric)
        self.assertEqual(metric.execution_id, "test-exec-001")
        self.assertEqual(metric.sheep_scores["S"], 75.0)

    def test_missing_gem_calculated(self):
        data = _make_metric(gem_score=None)
        data["sheep_scores"] = {"S": 80, "H": 80, "E1": 80, "E2": 80, "P": 80}
        metric = _json_to_metric(data)
        self.assertAlmostEqual(metric.gem_score, 80.0)


class TestMetricReader(unittest.TestCase):
    def test_load_from_temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            for i in range(3):
                fp = os.path.join(td, f"metric_{i}.json")
                with open(fp, "w") as f:
                    json.dump(_make_metric(execution_id=f"exec-{i}"), f)

            reader = MetricReader()
            metrics = reader.load_metrics(td)
            self.assertEqual(len(metrics), 3)

    def test_load_empty_dir(self):
        with tempfile.TemporaryDirectory() as td:
            reader = MetricReader()
            metrics = reader.load_metrics(td)
            self.assertEqual(metrics, [])

    def test_load_nonexistent_dir(self):
        reader = MetricReader()
        metrics = reader.load_metrics("/nonexistent/path")
        self.assertEqual(metrics, [])

    def test_load_skips_bad_json(self):
        with tempfile.TemporaryDirectory() as td:
            good = os.path.join(td, "good.json")
            bad = os.path.join(td, "bad.json")
            with open(good, "w") as f:
                json.dump(_make_metric(), f)
            with open(bad, "w") as f:
                f.write("not json")

            reader = MetricReader()
            metrics = reader.load_metrics(td)
            self.assertEqual(len(metrics), 1)

    def test_filter_by_skill(self):
        metrics = [
            _json_to_metric(_make_metric(skill_name="a")),
            _json_to_metric(_make_metric(skill_name="b")),
            _json_to_metric(_make_metric(skill_name="a")),
        ]
        reader = MetricReader()
        result = reader.filter_by_skill(metrics, "a")
        self.assertEqual(len(result), 2)

    def test_filter_by_time_window(self):
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(hours=48)).isoformat()
        new_ts = now.isoformat()

        metrics = [
            _json_to_metric(_make_metric(timestamp=old_ts)),
            _json_to_metric(_make_metric(timestamp=new_ts)),
        ]
        reader = MetricReader()
        result = reader.filter_by_time_window(metrics, hours=24)
        self.assertEqual(len(result), 1)

    def test_filter_by_workflow(self):
        metrics = [
            _json_to_metric(_make_metric(workflow="WORKFLOW_A")),
            _json_to_metric(_make_metric(workflow="WORKFLOW_B")),
        ]
        reader = MetricReader()
        result = reader.filter_by_workflow(metrics, "WORKFLOW_A")
        self.assertEqual(len(result), 1)


class TestMetricAggregator(unittest.TestCase):
    def _make_metrics(self, count: int, gem_base: float = 70.0) -> list:
        result = []
        for i in range(count):
            ts = (datetime.now(timezone.utc) - timedelta(hours=count - i)).isoformat()
            m = _json_to_metric(_make_metric(
                timestamp=ts,
                gem_score=gem_base + i * 0.5,
                sheep_scores={"S": 70 + i, "H": 65, "E1": 60, "E2": 55, "P": 70},
            ))
            result.append(m)
        return result

    def test_aggregate_gem(self):
        metrics = self._make_metrics(10)
        agg = MetricAggregator()
        stats = agg.aggregate_gem(metrics)
        self.assertEqual(stats["count"], 10)
        self.assertGreater(stats["mean"], 0)
        self.assertGreater(stats["std"], 0)

    def test_aggregate_by_dimension(self):
        metrics = self._make_metrics(10)
        agg = MetricAggregator()
        dim_stats = agg.aggregate_by_dimension(metrics)
        self.assertIn("S", dim_stats)
        self.assertEqual(dim_stats["S"]["count"], 10)

    def test_moving_average(self):
        agg = MetricAggregator()
        scores = [10, 20, 30, 40, 50]
        ma = agg.moving_average(scores, 3)
        self.assertEqual(len(ma), 3)
        self.assertAlmostEqual(ma[0], 20.0)

    def test_moving_average_too_short(self):
        agg = MetricAggregator()
        self.assertEqual(agg.moving_average([1, 2], 5), [])

    def test_trend_detection_declining(self):
        metrics = self._make_metrics(40, gem_base=80.0)
        # Override GEM scores to create declining trend
        for i, m in enumerate(metrics):
            object.__setattr__(m, "gem_score", 90 - i * 0.5)

        agg = MetricAggregator()
        result = agg.trend_detection(metrics)
        self.assertEqual(result["trend"], "declining")

    def test_trend_detection_stable(self):
        metrics = self._make_metrics(40, gem_base=70.0)
        # Keep all GEM scores the same
        for m in metrics:
            object.__setattr__(m, "gem_score", 70.0)

        agg = MetricAggregator()
        result = agg.trend_detection(metrics)
        self.assertEqual(result["trend"], "stable")


class TestDegradationDetector(unittest.TestCase):
    def test_no_alerts_with_few_metrics(self):
        metrics = [_json_to_metric(_make_metric()) for _ in range(3)]
        detector = DegradationDetector()
        alerts = detector.detect_degradation(metrics)
        self.assertEqual(alerts, [])

    def test_detects_critical(self):
        """Generate metrics where recent scores are much lower than historical."""
        metrics = []
        now = datetime.now(timezone.utc)
        # 20 good historical metrics
        for i in range(20):
            ts = (now - timedelta(hours=40 - i)).isoformat()
            metrics.append(_json_to_metric(_make_metric(
                timestamp=ts, gem_score=80.0,
                sheep_scores={"S": 80, "H": 80, "E1": 80, "E2": 80, "P": 80},
            )))
        # 10 bad recent metrics (below historical)
        for i in range(10):
            ts = (now - timedelta(hours=10 - i)).isoformat()
            metrics.append(_json_to_metric(_make_metric(
                timestamp=ts, gem_score=40.0,
                sheep_scores={"S": 40, "H": 40, "E1": 40, "E2": 40, "P": 40},
            )))

        detector = DegradationDetector()
        alerts = detector.detect_degradation(metrics)
        # Should detect degradation
        self.assertGreater(len(alerts), 0)
        severities = {a.severity for a in alerts}
        self.assertIn("critical", severities)

    def test_check_sheep_thresholds_ok(self):
        metrics = [_json_to_metric(_make_metric(
            sheep_scores={"S": 80, "H": 80, "E1": 80, "E2": 80, "P": 80},
            gem_score=80.0,
        ))]
        detector = DegradationDetector()
        alerts = detector.check_sheep_thresholds(metrics)
        self.assertEqual(len(alerts), 0)

    def test_check_sheep_thresholds_critical(self):
        metrics = [_json_to_metric(_make_metric(
            sheep_scores={"S": 40, "H": 40, "E1": 40, "E2": 40, "P": 40},
            gem_score=35.0,
        ))]
        detector = DegradationDetector()
        alerts = detector.check_sheep_thresholds(metrics)
        self.assertGreater(len(alerts), 0)


class TestReportGenerator(unittest.TestCase):
    def test_empty_metrics(self):
        gen = ReportGenerator()
        report = gen.generate_summary([], "24h")
        self.assertEqual(report["total_executions"], 0)

    def test_full_report(self):
        metrics = [_json_to_metric(_make_metric(
            sheep_scores={"S": 75, "H": 65, "E1": 60, "E2": 55, "P": 70},
            gem_score=65.0,
        )) for _ in range(5)]

        gen = ReportGenerator()
        report = gen.generate_summary(metrics, "24h")
        self.assertEqual(report["total_executions"], 5)
        self.assertIn("gem_summary", report)
        self.assertIn("dimension_table", report)

    def test_format_report(self):
        gen = ReportGenerator()
        report = gen.generate_summary([], "24h")
        text = gen.format_report(report)
        self.assertIn("SeekR Evolution Report", text)
        self.assertIn("No data available", text)


if __name__ == "__main__":
    unittest.main()
