"""SeekR shared data models, constants, and helper functions.

SHEEP framework: Semantic, Human-credibility, Evidence, Ecosystem, Performance.
All models use only Python stdlib.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# SHEEP Constants
# ---------------------------------------------------------------------------

DIMENSIONS: Dict[str, str] = {
    "S": "Semantic Coverage",
    "H": "Human Credibility",
    "E1": "Evidence Structuring",
    "E2": "Ecosystem Integration",
    "P": "Performance Monitoring",
}

DIMENSION_WEIGHTS: Dict[str, float] = {
    "S": 0.25,
    "H": 0.25,
    "E1": 0.20,
    "E2": 0.15,
    "P": 0.15,
}

CRITICAL_THRESHOLD: Dict[str, int] = {
    "S": 55,
    "H": 50,
    "E1": 45,
    "E2": 40,
    "P": 45,
}

WARNING_THRESHOLD: Dict[str, int] = {
    "S": 65,
    "H": 60,
    "E1": 55,
    "E2": 50,
    "P": 55,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def z_score(current: float, historical_mean: float, historical_std: float) -> float:
    """Calculate z-score. Returns 0.0 when std is 0 to avoid division by zero."""
    if historical_std == 0:
        return 0.0
    return (current - historical_mean) / historical_std


def gem_band(score: float) -> str:
    """Map a GEM score (0-100) to a letter band: A >= 85, B >= 70, C >= 55, D >= 40, F < 40."""
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def sheep_status(score: float, dimension: str) -> str:
    """Return OK / WARNING / CRITICAL for a dimension score."""
    if score < CRITICAL_THRESHOLD[dimension]:
        return "CRITICAL"
    if score < WARNING_THRESHOLD[dimension]:
        return "WARNING"
    return "OK"


def calculate_gem(scores: Dict[str, float]) -> float:
    """Calculate weighted GEM score from SHEEP dimension scores.

    Args:
        scores: Mapping of dimension keys (S, H, E1, E2, P) to raw scores.

    Returns:
        Weighted average in 0-100 range.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        if dim in scores:
            weighted_sum += scores[dim] * weight
            total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 2)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SheepScore:
    """Single SHEEP dimension score with weight applied."""
    dimension: str
    raw_score: float
    weight: float
    weighted_score: float


@dataclass(frozen=True)
class ExecutionMetric:
    """Record of a single skill execution with SHEEP scores."""
    execution_id: str
    timestamp: str  # ISO-8601
    workflow: str
    skill_name: str
    skill_version: str
    sheep_scores: Dict[str, float]  # {S: x, H: x, E1: x, E2: x, P: x}
    gem_score: float
    findings_count: int
    duration_ms: int
    error_count: int


@dataclass(frozen=True)
class DegradationAlert:
    """Flag raised when a dimension's z-score exceeds thresholds."""
    skill: str
    dimension: str
    z_score: float
    severity: Literal["warning", "critical"]
    trend: str  # e.g. "declining", "spike", "flat"


@dataclass(frozen=True)
class Strategy:
    """An evolution strategy proposed by the analytics engine."""
    strategy_id: str
    strategy_type: Literal["threshold", "trigger", "weight", "fallback", "content"]
    target_skill: str
    proposed_changes: str
    expected_gem_boost: float
    confidence: float
    status: Literal["proposed", "approved", "active", "retired", "rejected"]


@dataclass(frozen=True)
class ABTestConfig:
    """Configuration for an A/B test comparing two skill versions."""
    test_id: str
    skill_name: str
    control_version: str
    candidate_version: str
    traffic_split: float  # 0.0-1.0 fraction going to candidate
    min_sample_size: int
    max_duration_days: int
    significance_level: float  # e.g. 0.05


@dataclass(frozen=True)
class ABTestResult:
    """Outcome of a completed or in-progress A/B test."""
    test_id: str
    status: Literal["running", "completed", "inconclusive"]
    control_mean: float
    candidate_mean: float
    improvement_pct: float
    p_value: float
    confidence: float
    winner: Optional[Literal["control", "candidate", "none"]]


@dataclass(frozen=True)
class ParityCheck:
    """Single check in a parity verification suite."""
    name: str
    passed: bool
    message: str
    details: str


@dataclass(frozen=True)
class ParityReport:
    """Full parity verification report against a baseline."""
    version: str
    baseline: str
    passed: bool
    checks: List[ParityCheck]
    blockers: List[str]


@dataclass(frozen=True)
class EvolutionReport:
    """Top-level report produced each evolution cycle."""
    timestamp: str  # ISO-8601
    window: str  # e.g. "7d", "30d"
    sheep_trends: Dict[str, str]  # dimension -> trend description
    degradation_alerts: List[DegradationAlert]
    active_tests: List[ABTestConfig]
    proposed_strategies: List[Strategy]
    parity_summary: Optional[ParityReport]


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def new_execution_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_sheep_scores(raw: Dict[str, float]) -> List[SheepScore]:
    """Build a list of SheepScore objects from raw dimension scores."""
    result: List[SheepScore] = []
    for dim, score in raw.items():
        if dim in DIMENSION_WEIGHTS:
            w = DIMENSION_WEIGHTS[dim]
            result.append(SheepScore(
                dimension=dim,
                raw_score=score,
                weight=w,
                weighted_score=round(score * w, 2),
            ))
    return result
