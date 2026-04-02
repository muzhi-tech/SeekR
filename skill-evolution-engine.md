# SEO/GEO Skill Auto-Evolution Engine
## Architecture Design v1.0

**Date:** 2026-04-03
**Based on:** Clawd-Code Patterns (Prompt Routing + Reference Data Snapshots + Parity Audit)
**Goal:** Enable Skills to autonomously evolve based on execution data

---

## 1. Design Philosophy

The Evolution Engine treats Skills as **evolvable programs** rather than static assets. Each Skill has:
- A **reference data layer** (thresholds, templates, scoring rubrics) that can be versioned
- An **execution trace** that records inputs, outputs, and outcomes
- A **closed feedback loop** that analyzes traces, generates improvements, and validates them via A/B testing

The three Clawd-Code patterns map to:
- **Prompt Routing** → Routing rules in the Evolution Engine determine which Skill version handles which trigger
- **Reference Data Snapshots** → Every Skill version snapshots its reference data (quality gates, thresholds, scoring weights)
- **Parity Audit** → Continuous parity checks between Skill versions ensure no capability regression

---

## 2. Evolution Engine Core Components

### 2.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EVOLUTION ENGINE                                 │
│                                                                      │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐  │
│  │   Effect     │───▶│    Pattern       │───▶│    Strategy      │  │
│  │  Collector   │    │   Recognizer     │    │   Generator      │  │
│  └──────────────┘    └─────────────────┘    └──────────────────┘  │
│         │                    │                      │              │
│         │                    ▼                      ▼              │
│         │            ┌─────────────────┐    ┌──────────────────┐  │
│         │            │  Parity Audit   │◀───│  A/B Test        │  │
│         │            │  Monitor         │    │  Controller       │  │
│         │            └─────────────────┘    └──────────────────┘  │
│         │                    │                      │              │
│         ▼                    ▼                      ▼              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              VERSIONED SKILL REGISTRY                       │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │
│  │  │ v1.0.0  │→│ v1.1.0  │→│ v1.2.0  │→│ v2.0.0  │→...     │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │   │
│  │       │           │           │           │                 │   │
│  │   [snap]      [snap]      [snap]      [snap]              │   │
│  │   +traces    +traces     +traces     +traces               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component: Effect Collector

**Purpose:** Continuously gather execution data from every Skill invocation.

#### Data Points Collected

| Category | Field | Type | Description |
|----------|-------|------|-------------|
| **Execution Context** | `execution_id` | UUID | Unique invocation ID |
| | `skill_name` | string | Which skill was invoked |
| | `skill_version` | semver | Version of the skill used |
| | `trigger` | string | The exact trigger phrase matched |
| | `input_url` | string | Target URL (if applicable) |
| | `timestamp` | ISO8601 | When execution started |
| | `duration_ms` | integer | Total execution time |
| **Output Quality** | `score` | float | Primary output score (0-100) |
| | `subscores` | JSON | Category-level scores |
| | `findings_count` | JSON | {critical: N, high: N, medium: N, low: N} |
| | `output_length` | integer | Characters in output |
| **Routing** | `matched_rules` | JSON | Which routing rules matched |
| | `route_version` | semver | Routing engine version used |
| **Errors** | `error_count` | integer | Number of errors |
| | `error_types` | JSON | {timeout: N, parse: N, network: N} |
| | `fallback_used` | boolean | Whether graceful degradation triggered |
| **Feedback** | `user_rating` | int | User 1-5 rating (if provided) |
| | `user_feedback` | text | Free-text feedback |
| | `reinvoke_count` | int | Times user re-ran with same trigger |

#### Collection Mechanism

The Effect Collector integrates at the Skill execution layer:

```python
class EffectCollector:
    def __init__(self, storage_adapter):
        self.storage = storage_adapter  # SQLite/PostgreSQL

    def collect(self, execution: ExecutionContext) -> ExecutionTrace:
        trace = ExecutionTrace(
            execution_id=uuid4(),
            skill_name=execution.skill_name,
            skill_version=execution.version,
            trigger=execution.trigger,
            input_url=execution.input_url,
            timestamp=now(),
            duration_ms=execution.duration_ms,
            score=execution.output.score,
            subscores=execution.output.subscores,
            findings_count=execution.output.findings_count,
            output_length=len(execution.output.raw),
            matched_rules=execution.routing.matched_rules,
            route_version=execution.routing.version,
            error_count=len(execution.errors),
            error_types=self._categorize_errors(execution.errors),
            fallback_used=execution.fallback_triggered,
            user_rating=execution.feedback.rating,
            user_feedback=execution.feedback.text,
            reinvoke_count=execution.reinvoke_count,
        )
        self.storage.append(trace)
        return trace
```

#### Storage Schema

```sql
CREATE TABLE execution_traces (
    execution_id      TEXT PRIMARY KEY,
    skill_name         TEXT NOT NULL,
    skill_version      TEXT NOT NULL,
    trigger            TEXT NOT NULL,
    input_url          TEXT,
    timestamp          TIMESTAMPTZ NOT NULL,
    duration_ms        INTEGER NOT NULL,
    score              REAL,
    subscores          JSONB,
    findings_count      JSONB,
    output_length       INTEGER,
    matched_rules       JSONB,
    route_version       TEXT,
    error_count         INTEGER DEFAULT 0,
    error_types         JSONB,
    fallback_used       BOOLEAN DEFAULT FALSE,
    user_rating         INTEGER,
    user_feedback       TEXT,
    reinvoke_count      INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_traces_skill_time ON execution_traces(skill_name, timestamp);
CREATE INDEX idx_traces_trigger ON execution_traces(trigger);
CREATE INDEX idx_traces_version ON execution_traces(skill_name, skill_version);
```

### 2.3 Component: Pattern Recognizer

**Purpose:** Analyze execution traces to identify what works, what fails, and why.

#### Analysis Modules

**1. Scoring Pattern Analyzer**

Identifies which input characteristics correlate with high/low scores.

```python
class ScoringPatternAnalyzer:
    def analyze(self, traces: List[ExecutionTrace]) -> List[Pattern]:
        patterns = []

        # URL-based patterns
        url_patterns = self._find_url_patterns(traces)
        patterns.extend(url_patterns)

        # Trigger-based patterns
        trigger_patterns = self._find_trigger_patterns(traces)
        patterns.extend(trigger_patterns)

        # Temporal patterns
        temporal = self._find_temporal_patterns(traces)
        patterns.extend(temporal)

        # Error correlation patterns
        error_patterns = self._find_error_correlations(traces)
        patterns.extend(error_patterns)

        return patterns

    def _find_url_patterns(self, traces):
        """Find URL characteristics that correlate with scores."""
        # E.g., URLs with /blog/ score higher on content skills
        # E.g., URLs with /products/ score higher on schema skills
        pass

    def _find_trigger_patterns(self, traces):
        """Find trigger phrase variations that produce better outcomes."""
        # E.g., "geo audit" vs "full geo audit" scores
        pass
```

**2. Degradation Detector**

Automatically detects when a Skill version is performing worse than historical baseline.

```python
class DegradationDetector:
    THRESHOLD_STD = 2.0  # Standard deviations before flagging

    def detect(self, skill_name: str, window_hours: int = 168) -> List[DegradationEvent]:
        traces = self.storage.get_recent(skill_name, window_hours)
        baseline = self.storage.get_baseline(skill_name)

        current_mean = mean(t.score for t in traces if t.score is not None)
        current_std = stdev(t.score for t in traces if t.score is not None)

        z_score = (current_mean - baseline.mean) / baseline.std

        if z_score < -self.THRESHOLD_STD:
            return [DegradationEvent(
                skill=skill_name,
                severity="high" if z_score < -3 else "medium",
                z_score=z_score,
                current_mean=current_mean,
                baseline_mean=baseline.mean,
                affected_triggers=self._get_affected_triggers(traces)
            )]

        return []
```

**3. Trigger Effectiveness Analyzer**

Identifies which trigger phrases produce the best outcomes for each skill.

```python
class TriggerEffectivenessAnalyzer:
    def analyze(self, skill_name: str) -> Dict[str, TriggerMetrics]:
        traces = self.storage.get_by_skill(skill_name)

        trigger_metrics = {}
        for trigger, group in groupby(traces, key=lambda t: t.trigger):
            scores = [t.score for t in group if t.score is not None]
            trigger_metrics[trigger] = TriggerMetrics(
                trigger=trigger,
                invocations=len(group),
                avg_score=mean(scores) if scores else None,
                std_score=stdev(scores) if len(scores) > 1 else 0,
                avg_duration=mean(t.duration_ms for t in group),
                error_rate=sum(t.error_count > 0 for t in group) / len(group),
                user_rating_avg=mean(t.user_rating for t in group if t.user_rating)
            )

        return trigger_metrics
```

**4. Reference Data Drift Detector**

Monitors whether the reference data (thresholds, quality gates) is still aligned with actual outcomes.

```python
class ReferenceDataDriftDetector:
    def detect_drift(self, skill_name: str, version: str) -> List[DriftReport]:
        reports = []
        ref_data = self.storage.get_reference_snapshot(skill_name, version)

        for threshold_name, threshold_value in ref_data.thresholds.items():
            actual_distribution = self._get_actual_distribution(
                skill_name, threshold_name
            )
            drift_score = self._calculate_drift(
                threshold_value, actual_distribution
            )

            if drift_score > 0.15:  # 15% drift triggers warning
                reports.append(DriftReport(
                    skill=skill_name,
                    version=version,
                    threshold=threshold_name,
                    current_threshold=threshold_value,
                    actual_p95=actual_distribution['p95'],
                    actual_p99=actual_distribution['p99'],
                    drift_percentage=drift_score * 100
                ))

        return reports
```

### 2.4 Component: Strategy Generator

**Purpose:** Generate candidate improvements based on recognized patterns.

#### Strategy Types

| Strategy | Description | Example |
|----------|-------------|---------|
| **Threshold Adjustment** | Modify quality gate thresholds | "Increase minimum score for 'Good' from 60 to 65 based on recent performance" |
| **Trigger Refinement** | Split or merge trigger routing | "Split 'seo audit' into 'seo full audit' and 'seo quick audit'" |
| **Reference Data Update** | Update embedded reference values | "Update CWV thresholds to match Google 2026 targets" |
| **Fallback Enhancement** | Improve graceful degradation | "Add fallback for missing DataForSEO API" |
| **Scoring Weight Reallocation** | Adjust category weights | "Increase Content Quality weight from 20% to 23%" |
| **Template Revision** | Update output templates | "Change report format to include executive summary" |

#### Strategy Generation Algorithm

```python
class StrategyGenerator:
    def __init__(self, pattern_recognizer: PatternRecognizer):
        self.patterns = pattern_recognizer

    def generate_strategies(self, skill_name: str) -> List[CandidateStrategy]:
        candidates = []

        # Degradation-driven strategies
        degradations = self.patterns.detect_degradation(skill_name)
        for deg in degradations:
            candidates.extend(self._from_degradation(deg))

        # Drift-driven strategies
        drifts = self.patterns.detect_reference_drift(skill_name)
        for drift in drifts:
            candidates.extend(self._from_drift(drift))

        # Opportunity-driven strategies
        opportunities = self._find_opportunities(skill_name)
        for opp in opportunities:
            candidates.extend(self._from_opportunity(opp))

        # Sort by expected impact and feasibility
        candidates.sort(key=lambda c: c.expected_impact / c.feasibility, reverse=True)

        return candidates[:10]  # Top 10 candidates

    def _from_degradation(self, deg: DegradationEvent) -> List[CandidateStrategy]:
        strategies = []

        if deg.severity == "high":
            # Emergency: generate rollback strategy
            strategies.append(CandidateStrategy(
                type="rollback",
                description=f"Rollback {deg.skill} to previous stable version",
                rollback_target=self._find_stable_version(deg.skill),
                expected_impact=0.8,
                feasibility=0.9,
                risk="low"
            ))

        # Analyze which triggers are affected
        for trigger in deg.affected_triggers:
            strategies.append(CandidateStrategy(
                type="trigger_adjustment",
                description=f"Refine routing for trigger '{trigger}' due to degradation",
                modifications={
                    "add_alternatives": self._suggest_alternative_phrases(trigger),
                    "adjust_threshold": 0.1  # Lower match threshold by 10%
                },
                expected_impact=0.5,
                feasibility=0.7,
                risk="medium"
            ))

        return strategies

    def _from_drift(self, drift: DriftReport) -> List[CandidateStrategy]:
        return [CandidateStrategy(
            type="threshold_adjustment",
            description=f"Adjust {drift.threshold} from {drift.current_threshold} to {drift.actual_p95}",
            modifications={"threshold_name": drift.threshold, "new_value": drift.actual_p95},
            expected_impact=0.4,
            feasibility=0.85,
            risk="low"
        )]
```

### 2.5 Component: A/B Test Controller

**Purpose:** Validate candidate strategies through controlled experiments before full deployment.

#### A/B Test Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CREATE     │────▶│    RUN       │────▶│   ANALYZE    │────▶│  DECIDE      │
│   Variant    │     │   Parallel   │     │   Statistical│     │  Promote/    │
│   & Control  │     │   Execution  │     │   Significance│     │  Reject      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

#### Test Configuration

```python
@dataclass
class ABTestConfig:
    test_id: str
    skill_name: str
    strategy: CandidateStrategy
    control_version: str  # Current production version
    candidate_version: str  # Version with modifications

    # Statistical parameters
    min_sample_size: int = 100  # Minimum executions per variant
    confidence_level: float = 0.95
    minimum_detectable_effect: float = 0.05  # 5% improvement

    # Execution parameters
    traffic_split: float = 0.1  # 10% to candidate, 90% to control
    max_duration_hours: int = 168  # 1 week max
    early_stop_enabled: bool = True
    early_stop_threshold: float = 0.99  # Stop early if significance reached
```

#### Statistical Analysis

```python
class ABTestAnalyzer:
    def analyze(self, test_id: str) -> TestResult:
        test = self.storage.get_test(test_id)
        control_traces = self.storage.get_test_traces(test_id, "control")
        candidate_traces = self.storage.get_test_traces(test_id, "candidate")

        # Primary metric: score
        control_scores = [t.score for t in control_traces if t.score is not None]
        candidate_scores = [t.score for t in candidate_traces if t.score is not None]

        stat_result = self._t_test(control_scores, candidate_scores)

        # Secondary metrics
        secondary = self._analyze_secondary_metrics(test, control_traces, candidate_traces)

        return TestResult(
            test_id=test_id,
            status=self._determine_status(stat_result, secondary),
            control_mean=mean(control_scores),
            candidate_mean=mean(candidate_scores),
            improvement_pct=(mean(candidate_scores) - mean(control_scores)) / mean(control_scores) * 100,
            p_value=stat_result.p_value,
            confidence=stat_result.confidence,
            sample_size_control=len(control_scores),
            sample_size_candidate=len(candidate_scores),
            secondary_metrics=secondary,
            recommendation=self._make_recommendation(stat_result, secondary)
        )

    def _determine_status(self, stat, secondary) -> str:
        if stat.confidence < 0.95:
            return "inconclusive"
        if stat.p_value < 0.05 and mean(secondary['candidate']) > mean(secondary['control']):
            return "promote"
        return "reject"
```

---

## 3. Skill Version Evolution Protocol

### 3.1 Version Lifecycle

```
┌─────────┐    invoke     ┌─────────┐   validated   ┌─────────┐  promoted   ┌─────────┐
│  v1.0.0 │◀──────────────│ active  │◀──────────────│candidate│◀────────────│  stable │
│  (snap) │               │ (snap)  │               │ (snap)  │             │ (snap)  │
└─────────┘               └─────────┘               └─────────┘             └─────────┘
     │                         │                         │                        ▲
     │                    [degradation]            [A/B success]              │
     │                         │                         │                        │
     └─────────────────────────┴─────────────────────────┴────────────────────────┘
                                    rollback
```

### 3.2 Snapshot Structure

Every Skill version is snapshotted with:

```python
@dataclass
class SkillSnapshot:
    version: str  # Semver: major.minor.patch

    # Core files
    skill_file: str  # Path to SKILL.md
    agent_files: Dict[str, str]  # agent_name -> file content

    # Reference data (versioned separately)
    reference_data: ReferenceDataSnapshot

    # Metrics at creation
    baseline_metrics: BaselineMetrics

    # Provenance
    created_at: datetime
    created_by: str  # "evolution-engine" or "human"
    parent_version: str
    generation_reason: str  # "initial", "a/b_promote", "threshold_adjust", etc.

    # Validation
    parity_check_passed: bool
    parity_check_details: Dict
```

#### Reference Data Snapshot

```python
@dataclass
class ReferenceDataSnapshot:
    """Versioned copy of all tunable parameters in a Skill."""

    # Quality thresholds
    quality_thresholds: Dict[str, float] = {
        "score_good": 60.0,
        "score_excellent": 80.0,
        "score_critical": 30.0,
    }

    # Scoring weights
    scoring_weights: Dict[str, float] = {
        "technical": 0.22,
        "content": 0.23,
        "on_page": 0.20,
        "schema": 0.10,
        "performance": 0.10,
        "geo": 0.10,
        "images": 0.05,
    }

    # Content minimums (from quality-gates.md)
    content_minimums: Dict[str, int] = {
        "homepage": 500,
        "service_page": 800,
        "blog_post": 1500,
        "product_page": 300,
        "location_page": 500,
    }

    # Core Web Vitals thresholds
    cwv_thresholds: Dict[str, ThresholdSet] = {
        "lcp": ThresholdSet(good=2500, needs_improvement=4000, poor=4000),
        "inp": ThresholdSet(good=200, needs_improvement=500, poor=500),
        "cls": ThresholdSet(good=0.1, needs_improvement=0.25, poor=0.25),
    }

    # Timeouts and limits
    limits: Dict[str, Any] = {
        "crawl_timeout_seconds": 30,
        "max_pages_per_audit": 50,
        "rate_limit_delay_ms": 1000,
        "max_concurrent_requests": 5,
    }

    # Deprecation list (e.g., deprecated schema types)
    deprecated: List[str] = ["HowTo", "SpecialAnnouncement"]

    # Trigger routing rules
    trigger_rules: List[TriggerRule] = []
```

### 3.3 Parity Audit

Before any version is promoted to stable, a Parity Audit ensures no capabilities are lost.

```python
class ParityAuditor:
    """
    Compares new version against baseline to ensure no regression.
    Based on Clawd-Code's Parity Audit pattern.
    """

    def audit(self, new_version: SkillSnapshot, baseline_version: SkillSnapshot) -> ParityReport:
        checks = []

        # 1. Trigger coverage parity
        checks.append(self._check_trigger_coverage(new_version, baseline_version))

        # 2. Reference data parity (all keys present)
        checks.append(self._check_reference_completeness(new_version, baseline_version))

        # 3. Output format parity (same sections, same structure)
        checks.append(self._check_output_structure(new_version, baseline_version))

        # 4. Scoring parity (same categories, same score ranges)
        checks.append(self._check_scoring_parity(new_version, baseline_version))

        # 5. Capability parity (no features removed)
        checks.append(self._check_capability_parity(new_version, baseline_version))

        all_passed = all(c.passed for c in checks)

        return ParityReport(
            version=new_version.version,
            baseline=baseline_version.version,
            passed=all_passed,
            checks=checks,
            blockers=[c for c in checks if not c.passed],
            warnings=[c for c in checks if c.passed and c.warnings]
        )

    def _check_trigger_coverage(self, new_ver, baseline) -> ParityCheck:
        new_triggers = {r.trigger for r in new_ver.reference_data.trigger_rules}
        baseline_triggers = {r.trigger for r in baseline.reference_data.trigger_rules}

        missing = baseline_triggers - new_triggers
        if missing:
            return ParityCheck(
                name="trigger_coverage",
                passed=False,
                message=f"Missing triggers: {missing}"
            )
        return ParityCheck(name="trigger_coverage", passed=True)

    def _check_capability_parity(self, new_ver, baseline) -> ParityCheck:
        """
        Verify new version can handle all the same skill types as baseline.
        Run both versions on same test URLs and compare output categories.
        """
        test_urls = ["https://example.com", "https://example.com/blog"]

        baseline_outputs = self._run_version(baseline, test_urls)
        new_outputs = self._run_version(new_ver, test_urls)

        missing_categories = set()
        for url in test_urls:
            baseline_cats = set(baseline_outputs[url].keys())
            new_cats = set(new_outputs[url].keys())
            missing = baseline_cats - new_cats
            if missing:
                missing_categories.update(missing)

        if missing_categories:
            return ParityCheck(
                name="capability_parity",
                passed=False,
                message=f"Missing output categories: {missing_categories}"
            )

        return ParityCheck(name="capability_parity", passed=True)
```

### 3.4 Version History Recording

```python
class VersionHistory:
    def record(self, snapshot: SkillSnapshot):
        self.storage.insert_version(snapshot)

    def compare(self, v1: str, v2: str, skill_name: str) -> VersionDiff:
        snap1 = self.storage.get_version(skill_name, v1)
        snap2 = self.storage.get_version(skill_name, v2)

        return VersionDiff(
            skill=skill_name,
            from_version=v1,
            to_version=v2,
            reference_changes=self._diff_reference_data(snap1, snap2),
            file_changes=self._diff_files(snap1, snap2),
            metrics_changes=self._diff_metrics(snap1, snap2),
            rationale=snap2.generation_reason
        )

    def get_history(self, skill_name: str, limit: int = 20) -> List[VersionSummary]:
        """Return version history for a skill."""
        return self.storage.get_version_history(skill_name, limit)

    def get_current(self, skill_name: str) -> SkillSnapshot:
        """Get the current production version."""
        return self.storage.get_current_version(skill_name)
```

---

## 4. Automated Trigger Conditions

### 4.1 Trigger Categories

| Category | Trigger | Condition | Priority |
|----------|---------|-----------|----------|
| **Scheduled** | `scheduled_evolution` | Weekly (Sundays 2am UTC) or monthly | Low |
| **Degradation** | `score_degradation` | z-score < -2.0 for 24h | Critical |
| **Degradation** | `error_rate_spike` | Error rate > 2x baseline for 1h | High |
| **Degradation** | `latency_spike` | p95 latency > 2x baseline for 30min | Medium |
| **Parity** | `reference_drift` | >15% drift in any threshold | Medium |
| **A/B** | `ab_test_complete` | Statistical significance reached | High |
| **A/B** | `ab_test_timeout` | 168h elapsed without significance | Low |
| **Manual** | `operator_trigger` | Human requests evolution | Operator |
| **Threshold** | `low_sample_quality` | <50 samples in 30 days for a trigger | Low |

### 4.2 Trigger Implementation

```python
class EvolutionTrigger:
    def __init__(self, storage: Storage, notifier: Notifier):
        self.storage = storage
        self.notifier = notifier

    def check_all(self) -> List[EvolutionEvent]:
        events = []

        # Check each trigger category
        events.extend(self._check_scheduled())
        events.extend(self._check_degradation())
        events.extend(self._check_parity_drift())
        events.extend(self._check_ab_tests())
        events.extend(self._check_sample_quality())

        # Deduplicate by skill + type
        seen = set()
        unique_events = []
        for e in events:
            key = (e.skill_name, e.trigger_type, e.trigger_id)
            if key not in seen:
                seen.add(key)
                unique_events.append(e)

        return unique_events

    def _check_degradation(self) -> List[EvolutionEvent]:
        events = []

        for skill_name in self.storage.get_all_skills():
            # Score degradation
            deg = DegradationDetector(storage).detect(skill_name)
            if deg:
                events.append(EvolutionEvent(
                    skill_name=skill_name,
                    trigger_type="degradation",
                    trigger_id=f"deg_{deg[0].severity}_{skill_name}",
                    severity=deg[0].severity,
                    description=f"Score degradation detected: {deg[0].z_score:.2f} z-score",
                    evidence={"degradation": deg[0]},
                    auto_action=self._should_auto_act(deg[0])
                ))

            # Error rate spike
            error_spike = self._detect_error_spike(skill_name)
            if error_spike:
                events.append(EvolutionEvent(
                    skill_name=skill_name,
                    trigger_type="error_rate_spike",
                    trigger_id=f"err_{skill_name}",
                    severity="high",
                    description=f"Error rate {error_spike.current_rate:.1%} vs baseline {error_spike.baseline_rate:.1%}",
                    evidence={"spike": error_spike},
                    auto_action=True  # Auto-rollback for error spikes
                ))

        return events

    def _check_scheduled(self) -> List[EvolutionEvent]:
        """Check if it's time for scheduled evolution."""
        now = datetime.utcnow()

        # Weekly: Sundays 2am UTC
        if now.weekday() == 6 and now.hour == 2 and now.minute < 30:
            return [EvolutionEvent(
                skill_name="__all__",  # Run for all skills
                trigger_type="scheduled",
                trigger_id=f"weekly_{now.isocalendar()[1]}",
                severity="low",
                description="Weekly scheduled evolution check",
                auto_action=False  # Always require human review for scheduled
            )]

        # Monthly: First Sunday of month
        if self._is_first_sunday(now) and now.hour == 3:
            return [EvolutionEvent(
                skill_name="__all__",
                trigger_type="scheduled",
                trigger_id=f"monthly_{now.strftime('%Y_%m')}",
                severity="low",
                description="Monthly scheduled evolution check",
                auto_action=False
            )]

        return []

    def _should_auto_act(self, degradation: DegradationEvent) -> bool:
        """Determine if degradation is severe enough for auto-action."""
        if degradation.severity == "critical" and degradation.z_score < -3.0:
            return True  # Auto-rollback for severe degradation
        return False  # Require human review otherwise
```

### 4.3 Evolution Workflow

```python
class EvolutionWorkflow:
    def __init__(
        self,
        collector: EffectCollector,
        recognizer: PatternRecognizer,
        generator: StrategyGenerator,
        tester: ABTestController,
        parity_auditor: ParityAuditor,
        version_registry: VersionRegistry,
        notifier: Notifier
    ):
        self.collector = collector
        self.recognizer = recognizer
        self.generator = generator
        self.tester = tester
        self.parity_auditor = parity_auditor
        self.registry = version_registry
        self.notifier = notifier

    def run(self, event: EvolutionEvent) -> EvolutionResult:
        """
        Main entry point for evolution workflow.
        Returns detailed result of the evolution process.
        """

        # Step 1: For __all__, expand to per-skill events
        if event.skill_name == "__all__":
            skills = self.registry.get_all_skill_names()
            return [self.run(e) for e in [
                EvolutionEvent(**{**asdict(event), "skill_name": s}) for s in skills
            ]]

        # Step 2: Analyze patterns
        patterns = self.recognizer.analyze(event.skill_name)

        # Step 3: Generate strategies
        strategies = self.generator.generate_strategies(event.skill_name)

        if not strategies:
            return EvolutionResult(
                event=event,
                status="no_candidates",
                message="No improvement strategies generated",
                strategies_proposed=0
            )

        # Step 4: For degradation, auto-select best strategy
        if event.trigger_type == "degradation" and event.auto_action:
            selected_strategy = strategies[0]
            return self._execute_strategy(
                event, selected_strategy, skip_review=True
            )

        # Step 5: Otherwise, present to human for review
        return EvolutionResult(
            event=event,
            status="awaiting_review",
            strategies_proposed=strategies,
            patterns_found=patterns,
            message=f"Generated {len(strategies)} candidate strategies"
        )

    def _execute_strategy(
        self,
        event: EvolutionEvent,
        strategy: CandidateStrategy,
        skip_review: bool = False
    ) -> EvolutionResult:
        """
        Execute a validated strategy: create version, run A/B test.
        """

        # Step 1: Create candidate version
        candidate_version = self._create_candidate_version(
            event.skill_name, strategy
        )

        # Step 2: Parity audit
        parity_report = self.parity_auditor.audit(
            candidate_version,
            self.registry.get_current(event.skill_name)
        )

        if not parity_report.passed:
            return EvolutionResult(
                event=event,
                status="parity_failed",
                strategy=strategy,
                parity_report=parity_report,
                message=f"Parity check failed: {parity_report.blockers}"
            )

        # Step 3: Register candidate version
        self.registry.register_candidate(candidate_version)

        # Step 4: Start A/B test
        test_config = ABTestConfig(
            test_id=str(uuid4()),
            skill_name=event.skill_name,
            strategy=strategy,
            control_version=self.registry.get_current(event.skill_name).version,
            candidate_version=candidate_version.version,
            traffic_split=0.1 if not skip_review else 0.5
        )

        self.tester.start_test(test_config)

        # Step 5: Notify
        self.notifier.send(
            f"A/B test started for {event.skill_name} v{candidate_version.version}"
        )

        return EvolutionResult(
            event=event,
            status="ab_test_started",
            strategy=strategy,
            candidate_version=candidate_version.version,
            test_id=test_config.test_id,
            message=f"A/B test running (ID: {test_config.test_id})"
        )
```

---

## 5. Data Model

### 5.1 Core Entities

```python
# Core entities stored in Versioned Skill Registry

class ExecutionTrace(Timestamped):
    execution_id: UUID
    skill_name: str
    skill_version: str
    trigger: str
    input_url: Optional[str]
    timestamp: datetime
    duration_ms: int
    score: Optional[float]
    subscores: Dict[str, float]
    findings_count: Dict[str, int]
    output_length: int
    matched_rules: List[str]
    route_version: str
    error_count: int
    error_types: Dict[str, int]
    fallback_used: bool
    user_rating: Optional[int]
    user_feedback: Optional[str]
    reinvoke_count: int

class SkillVersion(Timestamped):
    version: str  # semver
    skill_name: str
    is_candidate: bool
    is_stable: bool
    parent_version: Optional[str]
    generation_reason: str
    created_at: datetime
    created_by: str  # "evolution-engine" or "human"
    reference_snapshot: ReferenceDataSnapshot
    parity_check_passed: bool

class ABTest(Timestamped):
    test_id: UUID
    skill_name: str
    control_version: str
    candidate_version: str
    strategy: Dict
    status: str  # "running", "promoted", "rejected", "timeout"
    traffic_split: float
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[TestResult]

class Pattern(Timestamped):
    pattern_id: UUID
    skill_name: str
    pattern_type: str  # "scoring", "trigger", "temporal", "error"
    description: str
    confidence: float
    evidence: Dict
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int

class TriggerRule(Timestamped):
    skill_name: str
    trigger_pattern: str
    routing_score: float
    fallback_skill: Optional[str]
    usage_count: int
    avg_score: Optional[float]
    is_active: bool
```

### 5.2 API Interface

```python
# Evolution Engine REST API (FastAPI)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Skill Evolution Engine API")

# === Version Registry ===

@app.get("/skills")
async def list_skills() -> List[SkillSummary]:
    """List all managed skills with current version and health."""

@app.get("/skills/{skill_name}")
async def get_skill(skill_name: str) -> SkillDetail:
    """Get detailed skill info including version history."""

@app.get("/skills/{skill_name}/versions")
async def list_versions(skill_name: str) -> List[VersionSummary]:
    """Get version history for a skill."""

@app.get("/skills/{skill_name}/versions/{version}")
async def get_version(skill_name: str, version: str) -> SkillVersion:
    """Get specific version details."""

@app.post("/skills/{skill_name}/rollback")
async def rollback_skill(skill_name: str, target_version: str) -> RollbackResult:
    """Rollback to a previous stable version."""

# === Execution Traces ===

@app.get("/traces")
async def query_traces(
    skill_name: Optional[str] = None,
    version: Optional[str] = None,
    trigger: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 100
) -> List[ExecutionTrace]:
    """Query execution traces with filters."""

@app.get("/traces/stats")
async def get_trace_stats(
    skill_name: str,
    window_hours: int = 168
) -> TraceStats:
    """Get aggregated statistics for a skill."""

# === Pattern Recognition ===

@app.get("/patterns")
async def list_patterns(
    skill_name: Optional[str] = None,
    pattern_type: Optional[str] = None,
    min_confidence: float = 0.5
) -> List[Pattern]:
    """List recognized patterns."""

@app.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: UUID) -> Pattern:
    """Get pattern details."""

# === A/B Tests ===

@app.get("/tests")
async def list_tests(
    skill_name: Optional[str] = None,
    status: Optional[str] = None
) -> List[ABTestSummary]:
    """List A/B tests."""

@app.get("/tests/{test_id}")
async def get_test(test_id: UUID) -> ABTestDetail:
    """Get A/B test details and current results."""

@app.post("/tests/{test_id}/promote")
async def promote_candidate(test_id: UUID) -> PromoteResult:
    """Manually promote candidate version."""

@app.post("/tests/{test_id}/reject")
async def reject_candidate(test_id: UUID, reason: str) -> RejectResult:
    """Manually reject candidate version."""

# === Evolution Triggers ===

@app.get("/triggers/status")
async def get_trigger_status() -> TriggerStatus:
    """Get current status of all trigger conditions."""

@app.post("/triggers/check")
async def run_trigger_check() -> List[EvolutionEvent]:
    """Manually trigger evolution check."""

@app.post("/evolution/run")
async def run_evolution(
    skill_name: str,
    strategy: CandidateStrategy,
    skip_review: bool = False
) -> EvolutionResult:
    """Manually trigger evolution for a specific strategy."""

# === Snapshot Management ===

@app.get("/skills/{skill_name}/snapshots/{version}")
async def get_snapshot(skill_name: str, version: str) -> SkillSnapshot:
    """Get full snapshot for a version."""

@app.post("/skills/{skill_name}/snapshots")
async def create_snapshot(
    skill_name: str,
    label: str,
    notes: Optional[str] = None
) -> SkillSnapshot:
    """Manually create a named snapshot."""

# === Parity Audit ===

@app.post("/skills/{skill_name}/parity-check")
async def run_parity_check(
    skill_name: str,
    new_version: str,
    baseline_version: str
) -> ParityReport:
    """Run parity check between two versions."""

# === Configuration ===

@app.get("/config")
async def get_config() -> EngineConfig:
    """Get evolution engine configuration."""

@app.patch("/config")
async def update_config(config: EngineConfig) -> EngineConfig:
    """Update evolution engine configuration."""
```

### 5.3 Storage Implementation

```python
# Storage adapter interface (implement for SQLite, PostgreSQL, etc.)

class StorageAdapter(Protocol):
    # Execution traces
    def append_trace(self, trace: ExecutionTrace) -> None: ...
    def get_traces(self, filters: TraceFilters) -> List[ExecutionTrace]: ...
    def get_trace_stats(self, skill: str, window: int) -> TraceStats: ...

    # Skill versions
    def register_version(self, version: SkillVersion) -> None: ...
    def get_version(self, skill: str, version: str) -> Optional[SkillVersion]: ...
    def get_current_version(self, skill: str) -> Optional[SkillVersion]: ...
    def get_version_history(self, skill: str, limit: int) -> List[SkillVersion]: ...
    def update_version_status(self, skill: str, version: str, status: str) -> None: ...

    # A/B tests
    def create_test(self, test: ABTest) -> None: ...
    def get_test(self, test_id: UUID) -> Optional[ABTest]: ...
    def update_test_result(self, test_id: UUID, result: TestResult) -> None: ...
    def append_test_trace(self, test_id: UUID, variant: str, trace: ExecutionTrace) -> None: ...

    # Patterns
    def record_pattern(self, pattern: Pattern) -> None: ...
    def get_patterns(self, filters: PatternFilters) -> List[Pattern]: ...

    # Snapshots
    def save_snapshot(self, snapshot: SkillSnapshot) -> None: ...
    def get_snapshot(self, skill: str, version: str) -> Optional[SkillSnapshot]: ...
```

---

## 6. Routing Engine Integration

### 6.1 Prompt Routing with Evolution

The Routing Engine uses versioned trigger rules to direct execution:

```python
class RoutingEngine:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    def route(self, trigger: str, context: ExecutionContext) -> RouteResult:
        # Get all active routing rules for this skill family
        rules = self._get_active_rules(context.skill_family)

        # Score each rule against the trigger
        scored_rules = []
        for rule in rules:
            score = self._calculate_match_score(trigger, rule)
            if score >= rule.min_score_threshold:
                scored_rules.append((score, rule))

        # Sort by score descending
        scored_rules.sort(key=lambda x: x[0], reverse=True)

        if not scored_rules:
            return RouteResult(
                routed_to=None,
                matched_rules=[],
                fallback=True,
                fallback_reason="no_matching_rules"
            )

        top_score, top_rule = scored_rules[0]

        # Check if score is close to second place (ambiguity)
        ambiguity_detected = (
            len(scored_rules) > 1 and
            scored_rules[0][0] - scored_rules[1][0] < 0.1
        )

        if ambiguity_detected:
            # Log ambiguity for pattern analysis
            self._record_ambiguity(trigger, scored_rules[:2])

        return RouteResult(
            routed_to=top_rule.skill_name,
            routed_to_version=top_rule.skill_version,
            matched_rules=[r for s, r in scored_rules[:3]],
            match_score=top_score,
            ambiguity_detected=ambiguity_detected
        )

    def _record_ambiguity(self, trigger: str, candidates: List[Tuple[float, TriggerRule]]):
        """Record routing ambiguity for pattern analysis."""
        self.storage.log_routing_ambiguity(
            trigger=trigger,
            candidates=[{
                "skill": r.skill_name,
                "version": r.skill_version,
                "score": s
            } for s, r in candidates]
        )
```

### 6.2 Dynamic Rule Evolution

When the Evolution Engine modifies trigger rules, the routing engine automatically picks them up:

```python
class EvolvedRoutingEngine(RoutingEngine):
    """
    Extension of RoutingEngine that integrates with Evolution Engine.
    Trigger rules are versioned alongside skill versions.
    """

    def _get_active_rules(self, skill_family: str) -> List[TriggerRule]:
        # Always use the current stable version's routing rules
        current = self.storage.get_current_version(skill_family)
        if not current:
            return self.storage.get_default_rules(skill_family)

        # Extract trigger rules from reference snapshot
        ref_data = current.reference_snapshot
        return ref_data.trigger_rules
```

---

## 7. Implementation Architecture

### 7.1 Directory Structure

```
~/.claude/
├── skills/
│   └── evolution-engine/
│       ├── SKILL.md                          # Main skill entry
│       ├── api/
│       │   ├── main.py                        # FastAPI application
│       │   ├── routers/
│       │   │   ├── skills.py
│       │   │   ├── traces.py
│       │   │   ├── patterns.py
│       │   │   ├── tests.py
│       │   │   └── evolution.py
│       │   └── models/
│       │       ├── __init__.py
│       │       ├── skill.py
│       │       ├── trace.py
│       │       ├── pattern.py
│       │       └── test.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── collector.py                  # Effect Collector
│       │   ├── recognizer.py                  # Pattern Recognizer
│       │   ├── generator.py                   # Strategy Generator
│       │   ├── tester.py                      # A/B Test Controller
│       │   ├── auditor.py                     # Parity Auditor
│       │   ├── router.py                      # Routing Engine
│       │   └── workflow.py                    # Evolution Workflow
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── adapter.py                     # StorageAdapter protocol
│       │   ├── sqlite.py                      # SQLite implementation
│       │   └── postgres.py                    # PostgreSQL implementation
│       ├── registry/
│       │   ├── __init__.py
│       │   ├── version_registry.py            # Version management
│       │   └── snapshot_manager.py            # Snapshot management
│       └── scripts/
│           ├── init_db.py                     # Database initialization
│           ├── backfill_traces.py            # Backfill historical traces
│           └── import_skill.py               # Import existing skill
├── skills-evolution-db/                       # Evolution database
│   └── evolution.db
└── skill_backups/                             # Skill snapshots
    └── {skill_name}/
        └── {version}/
            ├── SKILL.md
            ├── agents/
            └── reference_data.json
```

### 7.2 Skill Integration Points

For a Skill to be managed by the Evolution Engine, it needs:

**1. Manifest file** (`~/.claude/skills/{skill}/EVOLUTION.md`):

```yaml
name: seo-audit
version: 1.7.0
evolution_enabled: true

managed_files:
  - SKILL.md
  - agents/**

versioned_reference:
  - reference_data.json
  - references/

triggers:
  - "seo audit"
  - "full site audit"
  - "site health check"

quality_metrics:
  primary: score  # The main 0-100 score
  subscores:
    - technical
    - content
    - schema
    - on_page
  thresholds:
    score_good: 60
    score_excellent: 80
    score_critical: 30

auto_evolution:
  enabled: true
  min_sample_size: 50
  degradation_threshold: 2.0  # z-score
  drift_threshold: 0.15
```

**2. Execution wrapper** that calls the Effect Collector:

```python
# In skill execution layer
async def execute_skill(skill_name: str, input_data: dict, context: dict):
    collector = EffectCollector(storage_adapter)

    # Wrap execution
    with collector.collect_context(skill_name, context) as trace_ctx:
        result = await actual_skill_execution(input_data, context)
        trace_ctx.record_output(result)
        return result
```

---

## 8. Deployment & Operations

### 8.1 Deployment Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Light** | Effect Collector + local SQLite only | Single-user, local development |
| **Standard** | Full engine + SQLite | Small teams, single machine |
| **Production** | Full engine + PostgreSQL + Redis queue | Teams, production |
| **Cloud** | Full engine + managed PostgreSQL + cloud queue | Large scale, multi-tenant |

### 8.2 Evolution Schedule

| Frequency | What Runs | Who Reviews |
|-----------|-----------|-------------|
| **Real-time** | Effect Collection, Routing | N/A |
| **Hourly** | Degradation detection, error spike alerts | Auto-action for critical |
| **Daily** | Pattern analysis, trigger check | System notifications |
| **Weekly (Sunday)** | Full evolution cycle for all skills | Human review required |
| **Monthly** | Deep pattern analysis, major version planning | Human review required |

### 8.3 Rollback Protocol

```
Degradation Detected (z < -2.0 for 24h)
           │
           ▼
┌─────────────────────────┐
│ Auto-rollback to last   │
│ stable version?         │
│ (if z < -3.0)           │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     │ Yes         │ No
     ▼             ▼
┌─────────┐  ┌─────────────────────┐
│Immediate│  │ Alert + Human      │
│rollback │  │ Review Required    │
└─────────┘  └─────────────────────┘
```

### 8.4 Safety Guardrails

1. **Parity Check Gate**: No version can be promoted without passing parity audit
2. **Traffic Gating**: A/B tests start at 10% traffic, only increase after significance
3. **Rollback Buffer**: Last 3 stable versions always available for immediate rollback
4. **Human Review for Major Versions**: v2.0+ requires explicit human approval
5. **Audit Log**: All evolution actions logged with full traceability
6. **Capacity Checks**: Evolution engine monitors its own performance, alerts if overloaded

---

## 9. Extension Points

### 9.1 Custom Pattern Recognizers

```python
class CustomPatternRecognizer(ABC):
    @abstractmethod
    def analyze(self, traces: List[ExecutionTrace]) -> List[Pattern]:
        """Return recognized patterns from execution traces."""
        pass

# Register custom recognizer
evolution_engine.register_pattern_recognizer("competitor_aware", CompetitorPatternRecognizer())
```

### 9.2 Custom Strategy Generators

```python
class CustomStrategyGenerator(ABC):
    @abstractmethod
    def generate(self, patterns: List[Pattern], constraints: Dict) -> List[CandidateStrategy]:
        pass

evolution_engine.register_strategy_generator("conservative", ConservativeStrategyGenerator())
```

### 9.3 External Data Sources

```python
class ExternalDataAdapter(Protocol):
    async def get_keyword_data(self, keyword: str) -> KeywordMetrics: ...
    async def get_serp_features(self, keyword: str) -> SERPFeatures: ...
    async def get_backlink_data(self, domain: str) -> BacklinkMetrics: ...

# Inject into evolution engine for richer pattern analysis
evolution_engine.set_external_adapter(semrush_adapter)
```

---

## 10. Example Evolution Cycle

### Scenario: `seo-technical` skill degradation

**Hour 0:** `seo-technical v1.2.0` is running with 97% average score

**Day 1, Hour 0:**
- New test URLs with complex JavaScript frameworks added to sample set
- Average score drops to 91%

**Day 2, Hour 0:**
- Average score drops to 85%
- z-score reaches -2.3 (threshold crossed)

**Day 2, Hour 1:**
```
EvolutionTrigger fires:
  trigger_type: "score_degradation"
  severity: "medium"
  z_score: -2.3

PatternRecognizer analyzes:
  - Detects JS-heavy URLs scoring 40 points lower
  - Identifies "CSR" (client-side rendering) URLs as the issue
  - Finds that current SSR detection logic doesn't catch Next.js App Router

StrategyGenerator proposes:
  1. [HIGH] Add Next.js App Router detection to SSR checker
     expected_impact: 0.6, feasibility: 0.8, risk: low
  2. [MEDIUM] Lower SSR weight from 25% to 20% for CSR-tolerant scoring
     expected_impact: 0.3, feasibility: 0.9, risk: medium

ParityAuditor: v1.2.1 passes parity check (no capabilities removed)

Workflow: A/B test started
  - Control: v1.2.0 (90% traffic)
  - Candidate: v1.2.1 (10% traffic)
```

**Day 3, Hour 18:** (after 100+ executions per variant)

```
ABTestAnalyzer reports:
  Control mean: 84.3
  Candidate mean: 92.1
  Improvement: +9.3%
  p_value: 0.002
  Confidence: 97.8%
  Recommendation: PROMOTE

Operator reviews and approves promotion
```

**Day 3, Hour 19:**
```
VersionRegistry:
  - v1.2.1 promoted from candidate → stable
  - v1.2.0 marked as stable (previous)
  - Parity snapshot created for v1.2.1

Traffic shifted to 100% v1.2.1
```

**Day 3, Hour 20:**
```
Notification sent:
  "seo-technical v1.2.1 promoted. SSR detection improved for Next.js App Router.
   Average score recovered: 84.3 → 92.1 (+9.3%)."

VersionHistory recorded:
  - parent: v1.2.0
  - reason: "a/b_promote"
  - generation_reason: "degradation_detected__nextjs_detection"
```

---

*Document Version: 1.0*
*Last Updated: 2026-04-03*
