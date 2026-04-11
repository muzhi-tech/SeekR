"""SeekR Strategy Generator — proposes evolution strategies from degradation alerts and SHEEP trends.

Reads DegradationAlerts + trend data, emits ranked Strategy objects that the
A/B Test Controller can later pick up for validation.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from _path_setup import ensure_paths  # noqa: E402
ensure_paths()

from seekr.scripts.models import (
    DIMENSIONS,
    DIMENSION_WEIGHTS,
    DegradationAlert,
    Strategy,
)

# ---------------------------------------------------------------------------
# Hardcoded SHEEP-to-action mapping
# ---------------------------------------------------------------------------

SHEEP_TO_ACTION: Dict[str, Dict] = {
    "H": {
        "action": "Add author credential checks",
        "priority": "HIGH",
        "gem_boost": (3, 5),
    },
    "E1": {
        "action": "Strengthen FAQ Schema generation",
        "priority": "HIGH",
        "gem_boost": (2, 4),
    },
    "S": {
        "action": "Increase keyword density targets",
        "priority": "MEDIUM",
        "gem_boost": (2, 3),
    },
    "E2": {
        "action": "Add external citation recommendations",
        "priority": "MEDIUM",
        "gem_boost": (1, 2),
    },
    "P": {
        "action": "Add content freshness reminders",
        "priority": "LOW",
        "gem_boost": (1, 2),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return uuid.uuid4().hex[:10]


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# StrategyGenerator
# ---------------------------------------------------------------------------

class StrategyGenerator:
    """Proposes evolution strategies from degradation alerts and SHEEP trends."""

    def __init__(
        self,
        degradation_alerts: List[DegradationAlert],
        sheep_trends: Dict,
    ) -> None:
        self.degradation_alerts = degradation_alerts
        self.sheep_trends = sheep_trends  # {dim: {"direction": ..., "slope": ..., ...}}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self) -> List[Strategy]:
        """Generate and rank strategies from all signal sources."""
        raw: List[Strategy] = []

        # 1. Degradation-driven strategies
        for alert in self.degradation_alerts:
            raw.extend(self._from_degradation(alert))

        # 2. Trend-driven strategies
        for dim, trend_data in self.sheep_trends.items():
            if dim in DIMENSIONS:
                raw.extend(self._from_trend(dim, trend_data))

        # 3. Parameter drift strategies
        drift_data = self.sheep_trends.get("_drift", {})
        if drift_data:
            raw.extend(self._from_drift(drift_data))

        return self._rank_strategies(raw)

    # ------------------------------------------------------------------
    # Degradation-driven strategies
    # ------------------------------------------------------------------

    def _from_degradation(self, alert: DegradationAlert) -> List[Strategy]:
        strategies: List[Strategy] = []
        dim = alert.dimension
        mapping = SHEEP_TO_ACTION.get(dim)
        if mapping is None:
            return strategies

        base_action = mapping["action"]
        priority = mapping["priority"]
        lo, hi = mapping["gem_boost"]

        # Scale confidence by z-score magnitude and severity
        z_factor = min(abs(alert.z_score) / 3.0, 1.0)
        severity_factor = 1.0 if alert.severity == "critical" else 0.7
        confidence = _clamp(z_factor * severity_factor)

        # Estimate gem boost based on severity
        expected_boost = lo + (hi - lo) * z_factor

        # --- content strategy for H / E1 degradation ---
        if dim in ("H", "E1") and alert.trend == "declining":
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="content",
                target_skill=alert.skill,
                proposed_changes=(
                    f"{base_action}. "
                    f"Dimension {dim} is {alert.trend} (z={alert.z_score:.2f}, "
                    f"severity={alert.severity}). "
                    f"Priority: {priority}. Review author bios, schema markup, "
                    f"and citation quality for target content."
                ),
                expected_gem_boost=round(expected_boost, 2),
                confidence=round(confidence, 2),
                status="proposed",
            ))

        # --- weight reallocation when a dimension drags GEM ---
        if alert.severity == "critical":
            weight_donors = [
                d for d in DIMENSION_WEIGHTS
                if d != dim and DIMENSION_WEIGHTS[d] > 0.10
            ]
            if weight_donors:
                top_donor = sorted(
                    weight_donors, key=lambda d: DIMENSION_WEIGHTS[d], reverse=True
                )[0]
                strategies.append(Strategy(
                    strategy_id=_new_id(),
                    strategy_type="weight",
                    target_skill=alert.skill,
                    proposed_changes=(
                        f"Reallocate weight from {top_donor} "
                        f"(current {DIMENSION_WEIGHTS[top_donor]:.2f}) to {dim} "
                        f"(current {DIMENSION_WEIGHTS[dim]:.2f}) "
                        f"to compensate for critical degradation."
                    ),
                    expected_gem_boost=round(expected_boost * 0.6, 2),
                    confidence=round(confidence * 0.8, 2),
                    status="proposed",
                ))

        # --- threshold strategy when severity is warning ---
        if alert.severity == "warning":
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="threshold",
                target_skill=alert.skill,
                proposed_changes=(
                    f"Lower threshold sensitivity for {dim} dimension scoring. "
                    f"Current z-score {alert.z_score:.2f} indicates mild degradation — "
                    f"tighten scoring bands to catch further decline earlier."
                ),
                expected_gem_boost=round(expected_boost * 0.4, 2),
                confidence=round(confidence * 0.7, 2),
                status="proposed",
            ))

        # --- fallback strategy if error_count context exists ---
        if alert.trend == "spike":
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="fallback",
                target_skill=alert.skill,
                proposed_changes=(
                    f"Add fallback handling for {dim} dimension in {alert.skill}. "
                    f"Spike detected (z={alert.z_score:.2f}) — implement graceful "
                    f"degradation and cached response path."
                ),
                expected_gem_boost=round(lo * 0.5, 2),
                confidence=round(confidence * 0.6, 2),
                status="proposed",
            ))

        return strategies

    # ------------------------------------------------------------------
    # Trend-driven strategies
    # ------------------------------------------------------------------

    def _from_trend(self, dim: str, trend_data: Dict) -> List[Strategy]:
        strategies: List[Strategy] = []
        direction = trend_data.get("direction", "flat")
        slope = trend_data.get("slope", 0.0)
        error_count = trend_data.get("error_count", 0)

        # Only generate strategies for declining or volatile dimensions
        if direction not in ("declining", "volatile"):
            return strategies

        mapping = SHEEP_TO_ACTION.get(dim)
        if mapping is None:
            return strategies

        base_action = mapping["action"]
        lo, hi = mapping["gem_boost"]

        slope_factor = _clamp(abs(slope) / 5.0)
        confidence = _clamp(0.5 + slope_factor * 0.4)
        expected_boost = lo + (hi - lo) * slope_factor

        # --- trigger strategy for declining dimensions ---
        if direction == "declining":
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="trigger",
                target_skill=trend_data.get("skill", "unknown"),
                proposed_changes=(
                    f"Update trigger routing for {dim} ({DIMENSIONS.get(dim, dim)}). "
                    f"Trend slope = {slope:.2f}/period. {base_action}. "
                    f"Re-prioritize skills that influence this dimension."
                ),
                expected_gem_boost=round(expected_boost, 2),
                confidence=round(confidence, 2),
                status="proposed",
            ))

        # --- fallback strategy when error_count is elevated ---
        if error_count >= 3:
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="fallback",
                target_skill=trend_data.get("skill", "unknown"),
                proposed_changes=(
                    f"Improve error handling for {dim}-related operations. "
                    f"Error count = {error_count} in current window — add retry "
                    f"logic and fallback content paths."
                ),
                expected_gem_boost=round(lo * 0.5, 2),
                confidence=round(_clamp(0.4 + slope_factor * 0.3), 2),
                status="proposed",
            ))

        # --- weight reallocation for volatile dimensions ---
        if direction == "volatile":
            strategies.append(Strategy(
                strategy_id=_new_id(),
                strategy_type="weight",
                target_skill=trend_data.get("skill", "unknown"),
                proposed_changes=(
                    f"Smooth {dim} scoring by temporarily reducing its weight "
                    f"from {DIMENSION_WEIGHTS.get(dim, 0.15):.2f} to "
                    f"{max(DIMENSION_WEIGHTS.get(dim, 0.15) - 0.05, 0.05):.2f}. "
                    f"Volatile trend (slope variance high). Re-evaluate after next window."
                ),
                expected_gem_boost=round(lo * 0.3, 2),
                confidence=round(_clamp(0.35), 2),
                status="proposed",
            ))

        return strategies

    # ------------------------------------------------------------------
    # Parameter drift strategies
    # ------------------------------------------------------------------

    def _from_drift(self, drift_data: Dict) -> List[Strategy]:
        strategies: List[Strategy] = []
        for param, delta in drift_data.items():
            abs_delta = abs(delta)
            if abs_delta < 0.1:
                continue

            confidence = _clamp(abs_delta / 2.0)
            expected_boost = round(abs_delta * 1.5, 2)

            if "threshold" in param.lower() or "cutoff" in param.lower():
                strategies.append(Strategy(
                    strategy_id=_new_id(),
                    strategy_type="threshold",
                    target_skill="*",
                    proposed_changes=(
                        f"Parameter '{param}' has drifted by {delta:+.3f}. "
                        f"Recalibrate threshold to match current scoring distribution."
                    ),
                    expected_gem_boost=expected_boost,
                    confidence=round(confidence, 2),
                    status="proposed",
                ))
            elif "weight" in param.lower():
                strategies.append(Strategy(
                    strategy_id=_new_id(),
                    strategy_type="weight",
                    target_skill="*",
                    proposed_changes=(
                        f"Weight parameter '{param}' drifted by {delta:+.3f}. "
                        f"Renormalize dimension weights to maintain GEM balance."
                    ),
                    expected_gem_boost=expected_boost,
                    confidence=round(confidence * 0.8, 2),
                    status="proposed",
                ))
            elif "trigger" in param.lower():
                strategies.append(Strategy(
                    strategy_id=_new_id(),
                    strategy_type="trigger",
                    target_skill="*",
                    proposed_changes=(
                        f"Trigger parameter '{param}' drifted by {delta:+.3f}. "
                        f"Re-tune trigger sensitivity for accurate skill routing."
                    ),
                    expected_gem_boost=expected_boost,
                    confidence=round(confidence * 0.75, 2),
                    status="proposed",
                ))

        return strategies

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def _rank_strategies(self, strategies: List[Strategy]) -> List[Strategy]:
        """Sort strategies by expected_gem_boost * confidence, descending."""
        return sorted(
            strategies,
            key=lambda s: s.expected_gem_boost * s.confidence,
            reverse=True,
        )


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Mock degradation alerts
    alerts = [
        DegradationAlert(
            skill="geo-content-optimizer",
            dimension="H",
            z_score=-2.8,
            severity="critical",
            trend="declining",
        ),
        DegradationAlert(
            skill="schema-architect",
            dimension="E1",
            z_score=-1.9,
            severity="warning",
            trend="declining",
        ),
        DegradationAlert(
            skill="seo-audit",
            dimension="S",
            z_score=2.2,
            severity="warning",
            trend="spike",
        ),
    ]

    # Mock SHEEP trends
    trends: Dict[str, Dict] = {
        "H": {"direction": "declining", "slope": -3.5, "skill": "geo-content-optimizer", "error_count": 1},
        "E1": {"direction": "declining", "slope": -2.0, "skill": "schema-architect", "error_count": 0},
        "S": {"direction": "volatile", "slope": 1.8, "skill": "seo-audit", "error_count": 4},
        "P": {"direction": "flat", "slope": 0.1, "skill": "performance-reporter", "error_count": 0},
        "_drift": {
            "semantic_threshold": 0.35,
            "h_weight": -0.15,
            "trigger_sensitivity": 0.22,
            "unused_param": 0.01,  # below threshold, should be ignored
        },
    }

    gen = StrategyGenerator(alerts, trends)
    results = gen.generate()

    print(f"Generated {len(results)} strategies:\n")
    for i, s in enumerate(results, 1):
        score = s.expected_gem_boost * s.confidence
        print(f"  [{i}] {s.strategy_id}  type={s.strategy_type}  "
              f"skill={s.target_skill}  boost={s.expected_gem_boost}  "
              f"conf={s.confidence}  rank_score={score:.2f}")
        print(f"      {s.proposed_changes[:100]}...")
        print()
