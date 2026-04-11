"""SeekR A/B Test Controller.

Manages the lifecycle of A/B tests comparing control vs candidate skill
versions. Uses statistical analysis (z-test for large samples, t-test
approximation for small samples) to determine winners with configurable
confidence thresholds and automatic safety guardrails.

Pure Python stdlib only: math, statistics, hashlib.
"""

from __future__ import annotations

import hashlib
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional

from _path_setup import ensure_paths  # noqa: E402
ensure_paths()

from seekr.scripts.models import (
    ABTestConfig,
    ABTestResult,
    Strategy,
    new_execution_id,
    now_iso,
)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULTS = {
    "traffic_split": 0.1,
    "min_sample_size": 500,
    "max_duration_days": 14,
    "significance_level": 0.95,
    "early_stop_threshold": 0.99,
    "check_interval_hours": 4,
}

VALID_STATES = {"draft", "running", "monitoring", "completed", "stopped", "rolled_back"}

# z-value lookups for common confidence levels (two-tailed)
Z_TABLE = {
    0.90: 1.645,
    0.95: 1.960,
    0.99: 2.576,
    0.999: 3.291,
}


# ---------------------------------------------------------------------------
# Internal runtime state (not persisted — rebuild from logs as needed)
# ---------------------------------------------------------------------------

@dataclass
class _VariantData:
    """Accumulated observations for a single variant."""
    observations: List[float] = field(default_factory=list)
    error_count: int = 0


@dataclass
class _TestState:
    """Mutable runtime state for a single A/B test."""
    status: str = "draft"
    control: _VariantData = field(default_factory=_VariantData)
    candidate: _VariantData = field(default_factory=_VariantData)
    baseline_error_rate: float = 0.0
    created_at: str = ""
    started_at: str = ""
    needs_human_approval: bool = False


# ---------------------------------------------------------------------------
# ABTestController
# ---------------------------------------------------------------------------

class ABTestController:
    """Orchestrates A/B tests for SeekR skill evolution.

    Lifecycle: draft -> running -> [monitoring] -> completed | stopped | rolled_back
    """

    def __init__(self, config: ABTestConfig) -> None:
        self.config = config
        self._state = _TestState(created_at=now_iso())

    # ------------------------------------------------------------------
    # Lifecycle: create
    # ------------------------------------------------------------------

    @staticmethod
    def create_test(strategy: Strategy) -> ABTestController:
        """Create an A/B test from an approved strategy.

        The strategy must be in 'approved' status. A major-version candidate
        (version bump >= 1.0) sets a human-approval flag.
        """
        if strategy.status != "approved":
            raise ValueError(
                f"Strategy {strategy.strategy_id} status is '{strategy.status}', "
                f"expected 'approved'"
            )

        config = ABTestConfig(
            test_id=f"abt-{uuid.uuid4().hex[:8]}",
            skill_name=strategy.target_skill,
            control_version="current",
            candidate_version=strategy.proposed_changes[:60],
            traffic_split=DEFAULTS["traffic_split"],
            min_sample_size=DEFAULTS["min_sample_size"],
            max_duration_days=DEFAULTS["max_duration_days"],
            significance_level=DEFAULTS["significance_level"],
        )

        controller = ABTestController(config)

        # Detect major version change
        if _is_major_version_change(strategy):
            controller._state.needs_human_approval = True

        return controller

    # ------------------------------------------------------------------
    # Lifecycle: start
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Move from draft to running."""
        if self._state.status != "draft":
            raise ValueError(f"Cannot start test in '{self._state.status}' state")
        if self._state.needs_human_approval:
            raise ValueError("Test requires human approval before starting (major version change)")
        self._state.status = "running"
        self._state.started_at = now_iso()

    # ------------------------------------------------------------------
    # Variant assignment
    # ------------------------------------------------------------------

    def assign_variant(self, session_id: str) -> str:
        """Deterministically assign a session to control or candidate.

        Uses SHA-256 consistent hashing so the same session always gets
        the same variant across requests.
        """
        if self._state.status != "running":
            return "control"

        hash_input = f"{self.config.test_id}:{session_id}"
        digest = hashlib.sha256(hash_input.encode()).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF  # 0.0 – 1.0

        if bucket < self.config.traffic_split:
            return "candidate"
        return "control"

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_result(self, variant: str, gem_score: float, is_error: bool = False) -> None:
        """Record a test observation for the given variant."""
        if variant not in ("control", "candidate"):
            raise ValueError(f"Unknown variant: {variant}")

        data = self._state.control if variant == "control" else self._state.candidate
        data.observations.append(gem_score)

        if is_error:
            data.error_count += 1

        # Set baseline error rate from first control observations
        if variant == "control" and len(data.observations) >= 50 and self._state.baseline_error_rate == 0.0:
            self._state.baseline_error_rate = data.error_count / len(data.observations)

    # ------------------------------------------------------------------
    # Statistical analysis
    # ------------------------------------------------------------------

    def check_significance(self) -> ABTestResult:
        """Run statistical test and return current result.

        Uses z-test approximation when both variants have >= 30 samples,
        otherwise falls back to a simple difference check.
        """
        ctrl = self._state.control.observations
        cand = self._state.candidate.observations

        ctrl_n = len(ctrl)
        cand_n = len(cand)

        if ctrl_n < 2 or cand_n < 2:
            return ABTestResult(
                test_id=self.config.test_id,
                status="running",
                control_mean=0.0,
                candidate_mean=0.0,
                improvement_pct=0.0,
                p_value=1.0,
                confidence=0.0,
                winner=None,
            )

        ctrl_mean = _mean(ctrl)
        cand_mean = _mean(cand)
        ctrl_std = _std(ctrl)
        cand_std = _std(cand)

        improvement_pct = (
            ((cand_mean - ctrl_mean) / ctrl_mean) * 100.0
            if ctrl_mean != 0.0
            else 0.0
        )

        # Z-test for difference of means (large sample approximation)
        if ctrl_n >= 30 and cand_n >= 30:
            se = math.sqrt(
                (ctrl_std ** 2 / ctrl_n) + (cand_std ** 2 / cand_n)
            )
            if se == 0.0:
                z = 0.0
                p_value = 1.0
            else:
                z = (cand_mean - ctrl_mean) / se
                p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))
        else:
            # Small-sample fallback: Welch-like approximate t
            se = math.sqrt(
                (ctrl_std ** 2 / max(ctrl_n - 1, 1))
                + (cand_std ** 2 / max(cand_n - 1, 1))
            )
            if se == 0.0:
                z = 0.0
                p_value = 1.0
            else:
                z = (cand_mean - ctrl_mean) / se
                # Approximate p from normal CDF (conservative for small n)
                p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))

        confidence = 1.0 - p_value

        # Determine winner
        winner: Optional[str] = None
        test_status: Literal["running", "completed", "inconclusive"] = "running"

        min_n = min(ctrl_n, cand_n)
        if min_n >= self.config.min_sample_size:
            if confidence >= self.config.significance_level:
                winner = "candidate" if cand_mean > ctrl_mean else "control"
                test_status = "completed"
            else:
                test_status = "inconclusive"

        return ABTestResult(
            test_id=self.config.test_id,
            status=test_status,
            control_mean=round(ctrl_mean, 4),
            candidate_mean=round(cand_mean, 4),
            improvement_pct=round(improvement_pct, 2),
            p_value=round(p_value, 6),
            confidence=round(confidence, 6),
            winner=winner,
        )

    def confidence_interval(self, variant: str, level: float = 0.95) -> Dict[str, float]:
        """Calculate confidence interval for a variant's mean GEM score."""
        data = (
            self._state.control.observations
            if variant == "control"
            else self._state.candidate.observations
        )
        n = len(data)
        if n < 2:
            return {"lower": 0.0, "upper": 0.0, "mean": 0.0}

        m = _mean(data)
        s = _std(data)
        z = Z_TABLE.get(level, 1.96)
        margin = z * s / math.sqrt(n)
        return {
            "lower": round(m - margin, 4),
            "upper": round(m + margin, 4),
            "mean": round(m, 4),
        }

    # ------------------------------------------------------------------
    # Safety: early stop
    # ------------------------------------------------------------------

    def should_stop(self) -> Dict:
        """Evaluate whether the test should be stopped early.

        Triggers:
          - Confidence >= early_stop_threshold (default 0.99)
          - Catastrophic drop: z_score < -3.0 on GEM
          - Error rate > 2x baseline
          - Max duration exceeded
        """
        if self._state.status not in ("running", "monitoring"):
            return {"stop": False, "reason": None}

        ctrl = self._state.control.observations
        cand = self._state.candidate.observations

        # Check max duration
        if self._state.started_at:
            elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(self._state.started_at)
            if elapsed.days >= self.config.max_duration_days:
                return {"stop": True, "reason": "max_duration_exceeded"}

        # Need minimum data to evaluate
        if len(ctrl) < 30 or len(cand) < 30:
            return {"stop": False, "reason": None}

        ctrl_mean = _mean(ctrl)
        cand_mean = _mean(cand)
        ctrl_std = _std(ctrl)

        # Catastrophic drop: candidate z < -3.0
        if ctrl_std > 0:
            z = (cand_mean - ctrl_mean) / (ctrl_std / math.sqrt(len(cand)))
            if z < -3.0:
                return {"stop": True, "reason": f"catastrophic_drop: z={z:.2f}"}

        # High confidence stop
        result = self.check_significance()
        if result.confidence >= DEFAULTS["early_stop_threshold"]:
            return {"stop": True, "reason": f"high_confidence: {result.confidence:.4f}"}

        # Error rate guardrail
        if self._state.baseline_error_rate > 0 and len(cand) >= 30:
            cand_error_rate = self._state.candidate.error_count / len(cand)
            if cand_error_rate > 2.0 * self._state.baseline_error_rate:
                return {
                    "stop": True,
                    "reason": f"error_rate_exceeded: {cand_error_rate:.3f} > "
                              f"{2.0 * self._state.baseline_error_rate:.3f}",
                }

        return {"stop": False, "reason": None}

    # ------------------------------------------------------------------
    # Lifecycle: promote / rollback
    # ------------------------------------------------------------------

    def promote_winner(self) -> Dict:
        """Promote the winning variant based on significance results.

        Only promotes if the test has completed with a clear winner.
        """
        if self._state.status not in ("running", "monitoring"):
            return {"promoted": False, "reason": f"test in '{self._state.status}' state"}

        result = self.check_significance()
        if result.status != "completed" or result.winner is None:
            return {"promoted": False, "reason": "no_significant_winner"}

        self._state.status = "completed"
        winner_version = (
            self.config.candidate_version
            if result.winner == "candidate"
            else self.config.control_version
        )

        return {
            "promoted": True,
            "winner": result.winner,
            "version": winner_version,
            "improvement_pct": result.improvement_pct,
            "confidence": result.confidence,
        }

    def rollback(self) -> Dict:
        """Roll back to control variant and stop the test."""
        previous_status = self._state.status
        self._state.status = "rolled_back"

        return {
            "rolled_back": True,
            "test_id": self.config.test_id,
            "previous_status": previous_status,
            "control_version": self.config.control_version,
            "control_observations": len(self._state.control.observations),
            "candidate_observations": len(self._state.candidate.observations),
        }

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    @property
    def status(self) -> str:
        return self._state.status

    def summary(self) -> Dict:
        """Return a human-readable summary of the test state."""
        ctrl = self._state.control.observations
        cand = self._state.candidate.observations
        return {
            "test_id": self.config.test_id,
            "skill": self.config.skill_name,
            "status": self._state.status,
            "control_n": len(ctrl),
            "candidate_n": len(cand),
            "control_mean": round(_mean(ctrl), 2) if ctrl else 0.0,
            "candidate_mean": round(_mean(cand), 2) if cand else 0.0,
            "traffic_split": self.config.traffic_split,
            "needs_approval": self._state.needs_human_approval,
        }


# ---------------------------------------------------------------------------
# Pure helper functions (no external dependencies)
# ---------------------------------------------------------------------------

def _mean(data: List[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty lists."""
    if not data:
        return 0.0
    return sum(data) / len(data)


def _std(data: List[float]) -> float:
    """Population standard deviation. Returns 0.0 for < 2 samples."""
    if len(data) < 2:
        return 0.0
    m = _mean(data)
    variance = sum((x - m) ** 2 for x in data) / len(data)
    return math.sqrt(variance)


def _normal_cdf(z: float) -> float:
    """Approximate the standard normal CDF using the Abramowitz & Stegun formula.

    Maximum error < 7.5e-8, sufficient for our confidence calculations.
    """
    if z < -8.0:
        return 0.0
    if z > 8.0:
        return 1.0

    # Constants for A&S approximation 26.2.17
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if z >= 0 else -1
    z_abs = abs(z) / math.sqrt(2.0)
    t = 1.0 / (1.0 + p * z_abs)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z_abs * z_abs)
    return 0.5 * (1.0 + sign * y)


def _is_major_version_change(strategy: Strategy) -> bool:
    """Heuristic: check if the proposed changes look like a major version bump."""
    # Simple heuristic — if expected_gem_boost is very large, treat as major
    return strategy.expected_gem_boost >= 15.0


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random

    random.seed(42)

    # 1. Create a strategy and approve it
    strategy = Strategy(
        strategy_id="strat-demo-001",
        strategy_type="content",
        target_skill="geo-content-optimizer",
        proposed_changes="v2.0: enhanced entity extraction with LLM chain-of-thought",
        expected_gem_boost=8.5,
        confidence=0.85,
        status="approved",
    )

    # 2. Create test from strategy
    ctrl = ABTestController.create_test(strategy)
    print(f"Test created: {ctrl.config.test_id}")
    print(f"  Status: {ctrl.status}")
    print(f"  Skill:  {ctrl.config.skill_name}")
    print()

    # 3. Start the test
    ctrl.start()
    print(f"Test started: {ctrl.status}")
    print()

    # 4. Simulate traffic
    control_gem_mean = 72.0
    candidate_gem_mean = 76.5  # +6.25% improvement
    gem_std = 12.0

    for i in range(1200):
        session_id = f"session-{i:04d}"
        variant = ctrl.assign_variant(session_id)

        if variant == "control":
            score = random.gauss(control_gem_mean, gem_std)
        else:
            score = random.gauss(candidate_gem_mean, gem_std)

        score = max(0.0, min(100.0, score))
        ctrl.record_result(variant, score)

    # 5. Check results
    print("=== Test Summary ===")
    summary = ctrl.summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print()

    result = ctrl.check_significance()
    print("=== Significance Check ===")
    print(f"  Control mean:   {result.control_mean}")
    print(f"  Candidate mean: {result.candidate_mean}")
    print(f"  Improvement:    {result.improvement_pct}%")
    print(f"  P-value:        {result.p_value}")
    print(f"  Confidence:     {result.confidence}")
    print(f"  Winner:         {result.winner}")
    print(f"  Status:         {result.status}")
    print()

    # 6. Confidence intervals
    for v in ("control", "candidate"):
        ci = ctrl.confidence_interval(v)
        print(f"  {v} 95% CI: [{ci['lower']}, {ci['upper']}] (mean={ci['mean']})")
    print()

    # 7. Early stop check
    stop = ctrl.should_stop()
    print(f"Should stop: {stop}")
    print()

    # 8. Promote winner
    promotion = ctrl.promote_winner()
    print(f"Promotion result: {promotion}")
    print()

    # --- Test safety guardrail: catastrophic drop ---
    print("=== Safety Guardrail Test ===")
    bad_strategy = Strategy(
        strategy_id="strat-bad-001",
        strategy_type="threshold",
        target_skill="geo-content-optimizer",
        proposed_changes="v2.1: aggressive keyword stuffing",
        expected_gem_boost=-10.0,
        confidence=0.3,
        status="approved",
    )
    bad_ctrl = ABTestController.create_test(bad_strategy)
    bad_ctrl.start()

    for i in range(200):
        session_id = f"bad-session-{i:04d}"
        variant = bad_ctrl.assign_variant(session_id)
        if variant == "control":
            score = random.gauss(72.0, 10.0)
        else:
            score = random.gauss(50.0, 10.0)  # catastrophic drop
        bad_ctrl.record_result(variant, max(0.0, min(100.0, score)))

    stop_result = bad_ctrl.should_stop()
    print(f"  Catastrophic drop stop: {stop_result}")

    rb = bad_ctrl.rollback()
    print(f"  Rollback: {rb}")
