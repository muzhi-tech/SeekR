"""Unit tests for seekr.scripts.models."""

import sys
import unittest
from pathlib import Path

# Ensure project root is importable
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from seekr.scripts.models import (
    CRITICAL_THRESHOLD,
    DIMENSIONS,
    DIMENSION_WEIGHTS,
    WARNING_THRESHOLD,
    DegradationAlert,
    ExecutionMetric,
    ParityCheck,
    ParityReport,
    SheepScore,
    Strategy,
    ABTestConfig,
    ABTestResult,
    EvolutionReport,
    calculate_gem,
    gem_band,
    make_sheep_scores,
    new_execution_id,
    now_iso,
    sheep_status,
    z_score,
)


class TestConstants(unittest.TestCase):
    def test_dimensions_has_five_keys(self):
        self.assertEqual(len(DIMENSIONS), 5)
        for key in ("S", "H", "E1", "E2", "P"):
            self.assertIn(key, DIMENSIONS)

    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0)

    def test_critical_less_than_warning(self):
        for dim in DIMENSION_WEIGHTS:
            self.assertLess(CRITICAL_THRESHOLD[dim], WARNING_THRESHOLD[dim])


class TestZScore(unittest.TestCase):
    def test_zero_std(self):
        self.assertEqual(z_score(50.0, 50.0, 0.0), 0.0)

    def test_positive(self):
        result = z_score(80.0, 70.0, 5.0)
        self.assertAlmostEqual(result, 2.0)

    def test_negative(self):
        result = z_score(60.0, 70.0, 5.0)
        self.assertAlmostEqual(result, -2.0)

    def test_same_as_mean(self):
        self.assertAlmostEqual(z_score(70.0, 70.0, 10.0), 0.0)


class TestGemBand(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(gem_band(90), "A")
        self.assertEqual(gem_band(85), "A")
        self.assertEqual(gem_band(75), "B")
        self.assertEqual(gem_band(70), "B")
        self.assertEqual(gem_band(60), "C")
        self.assertEqual(gem_band(55), "C")
        self.assertEqual(gem_band(42), "D")
        self.assertEqual(gem_band(40), "D")
        self.assertEqual(gem_band(30), "F")
        self.assertEqual(gem_band(0), "F")

    def test_boundary(self):
        self.assertEqual(gem_band(84.99), "B")
        self.assertEqual(gem_band(39.99), "F")


class TestSheepStatus(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(sheep_status(80.0, "S"), "OK")

    def test_warning(self):
        self.assertEqual(sheep_status(60.0, "S"), "WARNING")

    def test_critical(self):
        self.assertEqual(sheep_status(50.0, "S"), "CRITICAL")

    def test_boundary_values(self):
        # Exactly at critical threshold
        self.assertEqual(sheep_status(float(CRITICAL_THRESHOLD["S"]), "S"), "WARNING")
        self.assertEqual(sheep_status(float(WARNING_THRESHOLD["S"]), "S"), "OK")


class TestCalculateGem(unittest.TestCase):
    def test_all_perfect(self):
        scores = {"S": 100, "H": 100, "E1": 100, "E2": 100, "P": 100}
        self.assertAlmostEqual(calculate_gem(scores), 100.0)

    def test_all_zero(self):
        scores = {"S": 0, "H": 0, "E1": 0, "E2": 0, "P": 0}
        self.assertAlmostEqual(calculate_gem(scores), 0.0)

    def test_partial_scores(self):
        # Only S and H
        scores = {"S": 80, "H": 60}
        expected = (80 * 0.25 + 60 * 0.25) / (0.25 + 0.25)
        self.assertAlmostEqual(calculate_gem(scores), round(expected, 2))

    def test_empty(self):
        self.assertEqual(calculate_gem({}), 0.0)

    def test_weighted_calculation(self):
        scores = {"S": 80, "H": 70, "E1": 60, "E2": 50, "P": 40}
        expected = (
            80 * 0.25 + 70 * 0.25 + 60 * 0.20 + 50 * 0.15 + 40 * 0.15
        )
        self.assertAlmostEqual(calculate_gem(scores), round(expected, 2))


class TestDataclasses(unittest.TestCase):
    def test_sheep_score_frozen(self):
        s = SheepScore(dimension="S", raw_score=75.0, weight=0.25, weighted_score=18.75)
        with self.assertRaises(AttributeError):
            s.raw_score = 80.0

    def test_execution_metric_creation(self):
        m = ExecutionMetric(
            execution_id="abc123",
            timestamp="2026-01-01T00:00:00Z",
            workflow="WORKFLOW_A",
            skill_name="test-skill",
            skill_version="1.0.0",
            sheep_scores={"S": 75, "H": 65},
            gem_score=70.0,
            findings_count=5,
            duration_ms=3000,
            error_count=0,
        )
        self.assertEqual(m.execution_id, "abc123")
        self.assertEqual(m.sheep_scores["S"], 75)

    def test_degradation_alert(self):
        a = DegradationAlert(
            skill="test", dimension="S", z_score=-2.5,
            severity="warning", trend="declining",
        )
        self.assertEqual(a.severity, "warning")

    def test_strategy_types(self):
        s = Strategy(
            strategy_id="s1", strategy_type="threshold", target_skill="sk",
            proposed_changes="test", expected_gem_boost=3.0,
            confidence=0.8, status="proposed",
        )
        self.assertEqual(s.strategy_type, "threshold")

    def test_ab_test_config(self):
        c = ABTestConfig(
            test_id="t1", skill_name="sk", control_version="v1",
            candidate_version="v2", traffic_split=0.1,
            min_sample_size=500, max_duration_days=14,
            significance_level=0.95,
        )
        self.assertEqual(c.traffic_split, 0.1)

    def test_ab_test_result(self):
        r = ABTestResult(
            test_id="t1", status="completed",
            control_mean=70.0, candidate_mean=75.0,
            improvement_pct=7.14, p_value=0.03,
            confidence=0.97, winner="candidate",
        )
        self.assertEqual(r.winner, "candidate")

    def test_parity_report(self):
        report = ParityReport(
            version="2.0", baseline="1.0", passed=True,
            checks=[ParityCheck(name="test", passed=True, message="ok", details="")],
            blockers=[],
        )
        self.assertTrue(report.passed)

    def test_evolution_report(self):
        r = EvolutionReport(
            timestamp="2026-01-01T00:00:00Z",
            window="24h",
            sheep_trends={"S": "stable"},
            degradation_alerts=[],
            active_tests=[],
            proposed_strategies=[],
            parity_summary=None,
        )
        self.assertEqual(r.window, "24h")


class TestFactoryHelpers(unittest.TestCase):
    def test_new_execution_id_length(self):
        eid = new_execution_id()
        self.assertEqual(len(eid), 12)
        self.assertTrue(eid.isalnum())

    def test_new_execution_id_unique(self):
        ids = {new_execution_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_now_iso_format(self):
        ts = now_iso()
        self.assertIn("T", ts)
        # Should be parseable
        from datetime import datetime
        datetime.fromisoformat(ts)

    def test_make_sheep_scores(self):
        raw = {"S": 80, "H": 70, "E1": 60, "E2": 50, "P": 40, "X": 99}
        scores = make_sheep_scores(raw)
        # X should be ignored
        self.assertEqual(len(scores), 5)
        for s in scores:
            self.assertIn(s.dimension, DIMENSION_WEIGHTS)
            self.assertAlmostEqual(s.weighted_score, round(s.raw_score * s.weight, 2))


if __name__ == "__main__":
    unittest.main()
