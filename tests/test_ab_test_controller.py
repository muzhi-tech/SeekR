"""Unit tests for seekr-evolve/scripts/ab_test_controller.py."""

import math
import random
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

from typing import Dict

 List

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
 sys.path.insert(0, _PROJECT_ROOT)

 _EVOLVE_SCRIPTS = str(Path(__file__).resolve().parent.parent / "seekr-evolve" / "scripts")
 if _EVOLVE_SCRIPTS not in sys.path:
 sys.path.insert(0, _EVOLVE_SCRIPTS)

 from seekr.scripts.models import ABTestConfig, ABTestResult, Strategy
 from ab_test_controller import ABTestController, DEFAULTS, _mean, _std, _normal_cdf, Z_TABLE


 # ===================================================================
# Helpers for building test instances
 # ===================================================================

def _make_strategy(**kw) -> Strategy:
 return Strategy(
     strategy_id="strat-test",
     strategy_type="content",
     target_skill="test-skill",
     proposed_changes="test change",
     expected_gem_boost=8.5,
     confidence=0.8,
     status="approved",
     **kw,
 )


def _make_controller() -> ABTestController:
     s = _make_strategy()
     return ABTestController.create_test(s)


 def _start_controller() -> ABTestController:
     s = _make_strategy()
     ctrl = ABTestController.create_test(s)
     ctrl.start()
     return ctrl


 # ===================================================================
# Tests for defaults and constants
 # ===================================================================

class TestDefaults(unittest.TestCase):
    def test_traffic_split(self):
        self.assertAlmostEqual(DEFAULTS["traffic_split"], 0.1)

    def test_min_sample_size(self):
        self.assertEqual(DEFAULTS["min_sample_size"], 500)
    def test_max_duration(self):
        self.assertEqual(DEFAULTS["max_duration_days"], 14)
    def test_significance_level(self):
        self.assertAlmostEqual(DEFAULTS["significance_level"], 0.95, places=2)
    def test_early_stop_threshold(self):
        self.assertAlmostEqual(DEFAULTS["early_stop_threshold"], 0.99, places=2)
    def test_check_interval(self):
        self.assertEqual(DEFAULTS["check_interval_hours"], 4)


class TestZTable(unittest.TestCase):
    def test_known_values(self):
        self.assertIn(0.90, Z_TABLE)
        self.assertAlmostEqual(Z_TABLE[0.90], 1.645)
        self.assertAlmostEqual(Z_TABLE[0.95], 1.960)
        self.assertAlmostEqual(Z_TABLE[0.99], 2.576)


# ===================================================================
# Tests for math helpers
# ===================================================================

class TestMathHelpers(unittest.TestCase):
    def test_mean_empty(self):
        self.assertEqual(_mean([]), 0.0)
    def test_mean_single(self):
        self.assertAlmostEqual(_mean([5.0]), 5.0)
    def test_mean_multiple(self):
        self.assertAlmostEqual(_mean([1.0, 2.0, 3.0, 4.0]), 2.5)
    def test_std_empty(self):
        self.assertEqual(_std([]), 0.0)
    def test_std_single(self):
        self.assertEqual(_std([5.0]), 0.0)
    def test_std_known(self):
        self.assertAlmostEqual(_std([2, 4, 4, 4, 5, 5, 7, 9]), 2.0)
    def test_normal_cdf_zero(self):
        self.assertAlmostEqual(_normal_cdf(0), 0.5, places=3)
    def test_normal_cdf_positive(self):
        self.assertAlmostEqual(_normal_cdf(1.96), 0.975, places=2)
    def test_normal_cdf_negative(self):
        self.assertAlmostEqual(_normal_cdf(-1.96), 0.025, places=2)
    def test_normal_cdf_extreme(self):
        self.assertAlmostEqual(_normal_cdf(-10), 0.0, places=4)
        self.assertAlmostEqual(_normal_cdf(10), 1.0, places=4)


# ===================================================================
# Tests for test creation
 # ===================================================================

class TestCreateTest(unittest.TestCase):
    def test_create_from_approved_strategy(self):
        s = _make_strategy()
        ctrl = ABTestController.create_test(s)
        self.assertIsInstance(ctrl, ABTestController)
        self.assertEqual(ctrl.status, "draft")
        self.assertTrue(ctrl.config.test_id.startswith("abt-"))
    def test_create_rejected_strategy_raises(self):
        s = _make_strategy(status="rejected")
        with self.assertRaises(ValueError):
            ABTestController.create_test(s)
    def test_major_version_sets_approval_flag(self):
        s = Strategy(
            strategy_id="strat-major",
            strategy_type="content",
            target_skill="test-skill",
            proposed_changes="v3.0",
            expected_gem_boost=20.0,
            confidence=0.8,
            status="approved",
        )
        ctrl = ABTestController.create_test(s)
        self.assertTrue(ctrl._state.needs_human_approval)


# ===================================================================
# Tests for lifecycle
# ===================================================================

class TestLifecycle(unittest.TestCase):
    def test_start_from_draft(self):
        ctrl = _start_controller()
        self.assertEqual(ctrl.status, "running")
    def test_start_wrong_state_raises(self):
        ctrl = _start_controller()
        ctrl._state.status = "running"
        with self.assertRaises(ValueError):
            ctrl.start()
    def test_start_with_approval_required_raises(self):
        s = Strategy(
            strategy_id="strat-major",
            strategy_type="content",
            target_skill="test-skill",
            proposed_changes="v3.0",
            expected_gem_boost=20.0,
            confidence=0.8,
            status="approved",
        )
        ctrl = ABTestController.create_test(s)
        with self.assertRaises(ValueError):
            ctrl.start()


# ===================================================================
# Tests for variant assignment
# ===================================================================

class TestVariantAssignment(unittest.TestCase):
    def test_consistent_hashing(self):
        ctrl = _start_controller()
        v1 = ctrl.assign_variant("session-1")
        v2 = ctrl.assign_variant("session-1")
        self.assertEqual(v1, v2)
    def test_not_running_returns_control(self):
        s = _make_strategy()
        ctrl = ABTestController.create_test(s)
        # Draft state — should return control
        self.assertEqual(ctrl.assign_variant("x"), "control")
    def test_completed_returns_control(self):
        ctrl = _start_controller()
        ctrl._state.status = "completed"
        self.assertEqual(ctrl.assign_variant("x"), "control")


# ===================================================================
# Tests for recording results
# ===================================================================

class TestRecording(unittest.TestCase):
    def test_record_control(self):
        ctrl = _start_controller()
        ctrl.record_result("control", 75.0)
        self.assertEqual(len(ctrl._state.control.observations), 1)
    def test_record_candidate(self):
        ctrl = _start_controller()
        ctrl.record_result("candidate", 80.0)
        self.assertEqual(len(ctrl._state.candidate.observations), 1)
    def test_record_invalid_variant_raises(self):
        ctrl = _start_controller()
        with self.assertRaises(ValueError):
            ctrl.record_result("bad_variant", 70.0)
    def test_record_with_error(self):
        ctrl = _start_controller()
        ctrl.record_result("candidate", 65.0, is_error=True)
        self.assertEqual(ctrl._state.candidate.error_count, 1)
        self.assertEqual(len(ctrl._state.candidate.observations), 1)
    def test_multiple_records(self):
        ctrl = _start_controller()
        for i in range(10):
            ctrl.record_result("control", 70.0 + i)
            ctrl.record_result("candidate", 75.0 + i)
        self.assertEqual(len(ctrl._state.control.observations), 10)
        self.assertEqual(len(ctrl._state.candidate.observations), 10)


# ===================================================================
# Tests for significance checking
# ===================================================================

class TestSignificance(unittest.TestCase):
    def test_insufficient_data(self):
        ctrl = _start_controller()
        result = ctrl.check_significance()
        self.assertEqual(result.status, "running")
        self.assertIsNone(result.winner)
    def test_significant_winner(self):
        random.seed(42)
        ctrl = _start_controller()
        for i in range(600):
            variant = ctrl.assign_variant(f"s-{i:04d}")
            if variant == "candidate":
                score = max(0.0, min(100.0, random.gauss(80, 5)))
            else:
                score = max(0.0, min(100.0, random.gauss(70, 5)))
            ctrl.record_result(variant, score)
        result = ctrl.check_significance()
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.winner, "candidate")
        self.assertGreater(result.improvement_pct, 0)
        self.assertGreater(result.confidence, 0.95)
    def test_confidence_interval(self):
        ctrl = _start_controller()
        for i in range(100):
            ctrl.record_result("control", max(0, min(100, random.gauss(70, 10))))
            ctrl.record_result("candidate", max(0, min(100, random.gauss(80, 10))))
        ci = ctrl.confidence_interval("control", 0.95)
        self.assertIn("lower", ci)
        self.assertIn("upper", ci)
        self.assertIn("mean", ci)
        self.assertGreater(ci["upper"], ci["lower"])
    def test_confidence_interval_insufficient_data(self):
        ctrl = _make_controller()
        ci = ctrl.confidence_interval("control", 0.95)
        self.assertEqual(ci["lower"], 0.0)
        self.assertEqual(ci["upper"], 0.0)
        self.assertEqual(ci["mean"], 0.0)


# ===================================================================
# Tests for should_stop
# ===================================================================

class TestShouldStop(unittest.TestCase):
    def test_no_stop_when_insufficient_data(self):
        ctrl = _start_controller()
        ctrl.record_result("control", 70.0)
        ctrl.record_result("candidate", 75.0)
        result = ctrl.should_stop()
        self.assertFalse(result["stop"])
  def test_high_confidence_stop(self):
        random.seed(42)
        ctrl = _start_controller()
        for i in range(600):
            variant = ctrl.assign_variant(f"s-{i:04d}")
            score = 80.0 if variant == "candidate" else 70.0
 30.0, max(0, min(100, score))
            ctrl.record_result(variant, score)
        result = ctrl.should_stop()
        self.assertTrue(result["stop"])
        self.assertIn("high_confidence", result["reason"])
    def test_max_duration_stop(self):
        ctrl = _make_controller()
        # Set start time to past
 max duration
        ctrl._state.started_at = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
 + "15 days")
        result = ctrl.should_stop()
        self.assertTrue(result["stop"])
        self.assertIn("max_duration_exceeded", result["reason"])
)


# ===================================================================
# Tests for promote/rollback
# ===================================================================

class TestPromoteRollback(unittest.TestCase):
    def test_promote_with_winner(self):
        random.seed(42)
        ctrl = _start_controller()
        for i in range(600):
            variant = ctrl.assign_variant(f"s-{i:04d}")
            score = 80.0 if variant == "candidate" else 70.0
 30.0, max(0, min(100, score))
            ctrl.record_result(variant, score)
        result = ctrl.promote_winner()
        self.assertTrue(result["promoted"])
        self.assertEqual(result["winner"], "candidate")
        self.assertGreater(result["improvement_pct"], 0)
        self.assertGreater(result["confidence"], 0.95)
  def test_promote_no_significant(self):
        ctrl = _start_controller()
        for i in range(50):
            ctrl.record_result("control", 70.0 + random.gauss(0, 1))
            ctrl.record_result("candidate", 70.0 + random.gauss(0, 1))
        result = ctrl.promote_winner()
        self.assertFalse(result["promoted"])
        self.assertIn("no_significant", result["reason"])
    def test_rollback(self):
        ctrl = _start_controller()
        result = ctrl.rollback()
        self.assertTrue(result["rolled_back"])
        self.assertEqual(result["control_version"], "v1")
    def test_rollback_preserves_observations(self):
        ctrl = _start_controller()
        for i in range(10):
            ctrl.record_result("control", 70.0)
            ctrl.record_result("candidate", 75.0)
        ctrl.rollback()
        self.assertEqual(len(ctrl._state.control.observations), 10)
        self.assertEqual(len(ctrl._state.candidate.observations), 10)


# ===================================================================
# Tests for summary
# ===================================================================

class TestSummary(unittest.TestCase):
    def test_summary_structure(self):
        random.seed(42)
        ctrl = _start_controller()
        for i in range(100):
            variant = ctrl.assign_variant(f"s-{i:04d}")
            score = 70.0 if variant == "candidate" else 80.0
 30.0, max(0, min(100, score))
            ctrl.record_result(variant, score)
        s = ctrl.summary()
        self.assertIn("test_id", s)
        self.assertEqual(s["control_n"], 108)
        self.assertEqual(s["candidate_n"], 20)


if __name__ == "__main__":
    unittest.main()
