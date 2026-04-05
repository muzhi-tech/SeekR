"""Unit tests for seekr-evolve/scripts/strategy_generator.py."""

import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_EVOLVE_SCRIPTS = str(Path(__file__).resolve().parent.parent / "seekr-evolve" / "scripts")
if _EVOLVE_SCRIPTS not in sys.path:
    sys.path.insert(0, _EVOLVE_SCRIPTS)

from seekr.scripts.models import DegradationAlert, Strategy

from strategy_generator import StrategyGenerator, SHEEP_TO_ACTION, _clamp


class TestClamp(unittest.TestCase):
    def test_within_range(self):
        self.assertAlmostEqual(_clamp(0.5), 0.5)

    def test_below(self):
        self.assertAlmostEqual(_clamp(-0.5), 0.0)

    def test_above(self):
        self.assertAlmostEqual(_clamp(1.5), 1.0)

    def test_custom_range(self):
        self.assertAlmostEqual(_clamp(5, 0, 10), 5)
        self.assertAlmostEqual(_clamp(-1, 0, 10), 0)
        self.assertAlmostEqual(_clamp(15, 0, 10), 10)


class TestSheepToAction(unittest.TestCase):
    def test_all_dimensions_mapped(self):
        from seekr.scripts.models import DIMENSION_WEIGHTS
        for dim in DIMENSION_WEIGHTS:
            self.assertIn(dim, SHEEP_TO_ACTION)
            self.assertIn("action", SHEEP_TO_ACTION[dim])
            self.assertIn("priority", SHEEP_TO_ACTION[dim])
            self.assertIn("gem_boost", SHEEP_TO_ACTION[dim])


class TestStrategyGeneratorBasic(unittest.TestCase):
    def test_empty_inputs(self):
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends={})
        result = gen.generate()
        self.assertEqual(result, [])

    def test_from_degradation_critical_h(self):
        alert = DegradationAlert(
            skill="test-skill", dimension="H", z_score=-3.5,
            severity="critical", trend="declining",
        )
        gen = StrategyGenerator(degradation_alerts=[alert], sheep_trends={})
        strategies = gen.generate()
        self.assertGreater(len(strategies), 0)

        types = {s.strategy_type for s in strategies}
        # Critical H should produce content + weight strategies
        self.assertIn("content", types)
        self.assertIn("weight", types)

        for s in strategies:
            self.assertEqual(s.status, "proposed")
            self.assertGreater(s.expected_gem_boost, 0)
            self.assertGreater(s.confidence, 0)

    def test_from_degradation_warning_e1(self):
        alert = DegradationAlert(
            skill="test-skill", dimension="E1", z_score=-2.3,
            severity="warning", trend="declining",
        )
        gen = StrategyGenerator(degradation_alerts=[alert], sheep_trends={})
        strategies = gen.generate()
        types = {s.strategy_type for s in strategies}
        self.assertIn("threshold", types)

    def test_from_degradation_spike(self):
        alert = DegradationAlert(
            skill="test-skill", dimension="S", z_score=2.5,
            severity="warning", trend="spike",
        )
        gen = StrategyGenerator(degradation_alerts=[alert], sheep_trends={})
        strategies = gen.generate()
        types = {s.strategy_type for s in strategies}
        self.assertIn("fallback", types)

    def test_unknown_dimension_ignored(self):
        alert = DegradationAlert(
            skill="test", dimension="X9", z_score=-3.0,
            severity="critical", trend="declining",
        )
        gen = StrategyGenerator(degradation_alerts=[alert], sheep_trends={})
        self.assertEqual(gen.generate(), [])


class TestStrategyGeneratorTrends(unittest.TestCase):
    def test_declining_trend_generates_trigger(self):
        trends = {
            "S": {"direction": "declining", "slope": -3.0, "skill": "seo-audit", "error_count": 0},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        self.assertGreater(len(strategies), 0)
        self.assertIn("trigger", {s.strategy_type for s in strategies})

    def test_stable_trend_no_strategies(self):
        trends = {
            "S": {"direction": "stable", "slope": 0.1, "skill": "seo-audit", "error_count": 0},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        self.assertEqual(gen.generate(), [])

    def test_volatile_trend_generates_weight(self):
        trends = {
            "P": {"direction": "volatile", "slope": 2.0, "skill": "perf", "error_count": 0},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        types = {s.strategy_type for s in strategies}
        self.assertIn("weight", types)

    def test_high_error_count_generates_fallback(self):
        trends = {
            "H": {"direction": "declining", "slope": -2.0, "skill": "test", "error_count": 5},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        types = {s.strategy_type for s in strategies}
        self.assertIn("fallback", types)


class TestStrategyGeneratorDrift(unittest.TestCase):
    def test_threshold_drift(self):
        trends = {
            "_drift": {"semantic_threshold": 0.35},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        self.assertGreater(len(strategies), 0)
        self.assertEqual(strategies[0].strategy_type, "threshold")

    def test_weight_drift(self):
        trends = {
            "_drift": {"h_weight": -0.20},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        self.assertGreater(len(strategies), 0)
        self.assertEqual(strategies[0].strategy_type, "weight")

    def test_trigger_drift(self):
        trends = {
            "_drift": {"trigger_sensitivity": 0.25},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        strategies = gen.generate()
        self.assertGreater(len(strategies), 0)
        self.assertEqual(strategies[0].strategy_type, "trigger")

    def test_small_drift_ignored(self):
        trends = {
            "_drift": {"tiny_param": 0.05},
        }
        gen = StrategyGenerator(degradation_alerts=[], sheep_trends=trends)
        self.assertEqual(gen.generate(), [])


class TestStrategyRanking(unittest.TestCase):
    def test_strategies_sorted_by_score(self):
        alerts = [
            DegradationAlert(
                skill="sk1", dimension="H", z_score=-3.5,
                severity="critical", trend="declining",
            ),
            DegradationAlert(
                skill="sk2", dimension="P", z_score=-2.1,
                severity="warning", trend="flat",
            ),
        ]
        gen = StrategyGenerator(degradation_alerts=alerts, sheep_trends={})
        strategies = gen.generate()
        if len(strategies) >= 2:
            scores = [s.expected_gem_boost * s.confidence for s in strategies]
            self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
