---
name: seekr-evolve
description: |
  Self-evolution engine for SEO/GEO skills. Monitors skill execution metrics (SHEEP/GEM scores),
  detects performance degradation patterns, generates optimization strategies, and validates them
  via A/B testing before promotion. Consumes metrics from seo-geo-master-orchestrator's
  execution logs and outputs optimization suggestions or automatic version promotions.
  Triggers: "evolve", "optimize skills", "check skill health", "run parity audit", "trigger evolution".
  This skill is the meta-layer that makes the SEO/GEO skill system self-improving.
license: CC BY-NC-SA 4.0
version: 1.0.0
tags: [evolution, skill-optimization, metrics, ab-testing, self-improving, seo, geo]
trigger-conditions:
  - evolution-requested
  - skill-optimization-requested
  - parity-check-requested
  - degradation-detected
  - scheduled-evolution
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# SEO/GEO Evolution Engine

## Purpose

The Evolution Engine is the **meta-layer** that makes the SEO/GEO skill system self-improving. It:
1. Consumes execution metrics written by seo-geo-master-orchestrator
2. Detects performance degradation via Pattern Recognition
3. Generates optimization strategies via Strategy Generator
4. Validates strategies via A/B Testing
5. Promotes winning versions via Snapshot Versioning
6. Runs Parity Audits to prevent capability regression

**Silent execution protocol — never ask, never stop, always complete.**

## Silent Execution Protocol

```
1. DO NOT ask for confirmation to run evolution cycles.
2. Use defined defaults for all missing data (thresholds, weights, etc.).
3. Generate full output in one pass — no iterative "should I continue?" prompts.
4. If a component fails, log the failure and continue with available data.
5. Always produce a complete parity audit or evolution report.
6. Auto-rollback if z-score < -3.0; require human for major version promotions.
```

---

## Part 1: Effect Collector

### 1.1 Data Collection Sources

```
Sources:
1. evolution-metrics/<execution_id>.json (from seo-geo-master-orchestrator)
   → Every workflow execution produces this file

2. Manual trigger (via this skill)
   → /seo-geo-evolution-engine evolve

3. Scheduled trigger (daily at 03:00 UTC)
   → Automated evolution cycle
```

### 1.2 Metrics Collected per Execution

```json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | WORKFLOW_D",
  "skill_name": "string",
  "skill_version": "semver",
  "trigger": "string",
  "input_url": "string",
  "duration_ms": 0,
  "score": 0-100,
  "sheep_scores": {
    "S_semantic_coverage": { "raw": 0-100, "weight": 0.25 },
    "H_human_credibility": { "raw": 0-100, "weight": 0.25 },
    "E1_evidence_structuring": { "raw": 0-100, "weight": 0.20 },
    "E2_ecosystem_integration": { "raw": 0-100, "weight": 0.15 },
    "P_performance_monitoring": { "raw": 0-100, "weight": 0.15 }
  },
  "gem_score": 0-100,
  "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "output_length": 0,
  "error_count": 0,
  "error_types": { "timeout": 0, "parse": 0, "network": 0 },
  "fallback_used": false,
  "user_rating": null,
  "articles_generated": 0,
  "pages_crawled": 0
}
```

### 1.3 Storage

```
Directory: seekr/evolution-metrics/
Format: <execution_id>.json (one file per execution)
Aggregation: Daily/weekly rollups for trend analysis
Retention: Raw: 90 days, Aggregated: 2 years
```

---

## Part 2: Pattern Recognizer

### 2.1 Detection Modules

#### Degradation Detector (z-score method)

```
Trigger: z-score < -2.0 for 24h window
Action: Log degradation alert, queue for Pattern Recognizer analysis

z-score formula:
  z = (current_avg - historical_avg) / historical_stddev
  Where:
    current_avg = average GEM score over last 24h
    historical_avg = average GEM score over last 30 days
    historical_stddev = standard deviation over last 30 days
```

#### Trend Analyzer (SHEEP dimension tracking)

```
Per dimension (S, H, E1, E2, P):
  1. Calculate 7-day moving average
  2. Calculate 30-day moving average
  3. If 7-day avg < 30-day avg - 10%: flag as declining
  4. If declining for 3+ consecutive days: trigger strategy generation

SHEEP dimension thresholds:
  - S_semantic_coverage < 65: flag (H, E1, E2, P similar)
  - H_human_credibility < 60: critical (direct impact on citation rate)
  - E1_evidence_structuring < 55: critical (direct impact on AI overview)
  - E2_ecosystem_integration < 50: high priority
  - P_performance_monitoring < 55: high priority
```

#### Trigger Effectiveness Analyzer

```
For each trigger phrase:
  1. Collect last 100 executions
  2. Calculate: avg_score, success_rate, avg_duration_ms
  3. Rank triggers by: score / (duration_ms / 1000)
  4. If trigger effectiveness dropped > 20%: flag for refinement
```

#### Reference Data Drift Detector

```
Monitor for drift in:
  - Ranking thresholds (what score = "high competition")
  - Weight configurations (SHEEP weights)
  - Platform-specific parameters (from platforms.json)

Drift detection:
  If any parameter drifted > 15% from baseline: flag for review
```

### 2.2 Pattern Recognition Output

```json
{
  "timestamp": "ISO8601",
  "analysis_window": "24h | 7d | 30d",
  "degradation_detected": {
    "skill": "string",
    "metric": "gem_score | sheep_dimension",
    "z_score": -2.5,
    "severity": "warning | critical",
    "trend": "declining | stable | improving"
  },
  "sheep_dimension_trends": {
    "S_semantic_coverage": { "trend": "declining", "change_pct": -8.2 },
    "H_human_credibility": { "trend": "stable", "change_pct": 1.1 },
    "E1_evidence_structuring": { "trend": "declining", "change_pct": -12.4 },
    "E2_ecosystem_integration": { "trend": "stable", "change_pct": 0.5 },
    "P_performance_monitoring": { "trend": "declining", "change_pct": -6.8 }
  },
  "trigger_effectiveness": [
    { "trigger": "audit my site", "avg_score": 72.3, "success_rate": 0.95, "rank": 1 },
    { "trigger": "GEO article", "avg_score": 68.1, "success_rate": 0.88, "rank": 2 }
  ],
  "recommendation": "GENERATE_STRATEGY | RUN_PARITY | MONITOR | NONE"
}
```

---

## Part 3: Strategy Generator

### 3.1 Strategy Types

| Type | Description | When to Use |
|---|---|---|
| **Threshold Adjustment** | Adjust scoring thresholds based on observed drift | Reference data drift detected |
| **Trigger Refinement** | Update trigger word weights or add/remove triggers | Trigger effectiveness dropped |
| **SHEEP Weight Reallocation** | Shift weight from high-scoring to low-scoring dimensions | One dimension consistently drags GEM down |
| **Fallback Enhancement** | Improve error handling for frequent failure patterns | error_count or fallback_used elevated |
| **Content Strategy** | Recommend focus areas for Workflow D | SHEEP dimensions consistently low (H, E1 most impactful) |

### 3.2 SHEEP Dimension → Action Mapping

```
H_human_credibility declining:
  → Strategy: "Add author credential checks to seo-content-writer"
  → Priority: HIGH (25% weight, direct citation impact)
  → Expected GEM boost: +3-5 points

E1_evidence_structuring declining:
  → Strategy: "Strengthen FAQ Schema generation in Workflow D"
  → Priority: HIGH (20% weight, direct AI Overview impact)
  → Expected GEM boost: +2-4 points

S_semantic_coverage declining:
  → Strategy: "Increase keyword density targets in content briefs"
  → Priority: MEDIUM (25% weight)
  → Expected GEM boost: +2-3 points

E2_ecosystem_integration declining:
  → Strategy: "Add external citation recommendations to content output"
  → Priority: MEDIUM (15% weight)
  → Expected GEM boost: +1-2 points

P_performance_monitoring declining:
  → Strategy: "Add content freshness reminders to tracking"
  → Priority: LOW (15% weight)
  → Expected GEM boost: +1-2 points
```

### 3.3 Strategy Generation Output

```json
{
  "strategy_id": "uuid",
  "timestamp": "ISO8601",
  "triggered_by": "pattern_recognition_output_id",
  "target_skill": "seo-content-writer",
  "strategy_type": "SHEEP_WEIGHT_REALLOCATION | THRESHOLD_ADJUSTMENT | FALLBACK_ENHANCEMENT | CONTENT_STRATEGY",
  "current_parameters": {
    "min_word_count": 1500,
    "required_citations": 5,
    "sheep_weights": { "S": 0.25, "H": 0.25, "E1": 0.20, "E2": 0.15, "P": 0.15 }
  },
  "proposed_changes": [
    {
      "parameter": "author_credential_required",
      "current_value": false,
      "proposed_value": true,
      "change_type": "add",
      "rationale": "H_dimension declining, +40% citation effect per platforms.json"
    }
  ],
  "expected_impact": {
    "sheep_dimension": "H_human_credibility",
    "expected_gem_boost": 3.5,
    "confidence": 0.78,
    "affected_workflows": ["WORKFLOW_D"]
  },
  "risk_assessment": {
    "overall_risk": "low | medium | high",
    "potential_drawbacks": ["Slight increase in content generation time"],
    "rollback_plan": "Revert to previous parameters within 24h if GEM drops"
  },
  "status": "PROPOSED | APPROVED | REJECTED | TESTING | PROMOTED"
}
```

---

## Part 4: A/B Testing Framework

### 4.1 Test Configuration

```
Default test configuration:
  - traffic_split: 90% control / 10% candidate (gradual rollout)
  - minimum_sample_size: 500 per variant
  - maximum_duration_days: 14
  - significance_level: 0.95 (p < 0.05)
  - early_stop_threshold: 0.99
  - test_metric: gem_score (primary)
```

### 4.2 Test Lifecycle

```
1. CREATE: Strategy approved → create A/B test with control + candidate
2. RUNNING: Traffic split, metrics collected per variant
3. MONITOR: Check significance every 4h
4. STOP: Auto-stop if:
     - Significance reached (p < 0.05) → promote winner
     - Loser detected (candidate significantly worse) → stop and rollback
     - Duration exceeded (14 days) → manual review
     - Catastrophic drop (z-score < -3.0 on any metric) → auto-rollback
5. REPORT: Generate test report with statistics
```

### 4.3 A/B Test Output Schema

```json
{
  "test_id": "uuid",
  "strategy_id": "uuid",
  "status": "running | completed | stopped | rolled_back",
  "variants": [
    {
      "variant_id": "control",
      "traffic_percentage": 90,
      "sample_size": 523,
      "metrics": {
        "gem_score": { "mean": 68.2, "stddev": 12.1 },
        "h_human_credibility": { "mean": 64.5, "stddev": 15.3 }
      }
    },
    {
      "variant_id": "candidate",
      "traffic_percentage": 10,
      "sample_size": 58,
      "metrics": {
        "gem_score": { "mean": 71.8, "stddev": 11.4 },
        "h_human_credibility": { "mean": 68.2, "stddev": 14.1 }
      }
    }
  ],
  "statistics": {
    "p_value": 0.023,
    "confidence": 0.977,
    "effect_size": 3.6,
    "recommendation": "promote_candidate"
  },
  "winner": "candidate | control | inconclusive",
  "promotion_timestamp": "ISO8601 (if promoted)"
}
```

---

## Part 5: Snapshot Versioning

### 5.1 Version Lifecycle

```
draft → candidate → stable → archived
                      ↑
              promoted by A/B test
              or manual approval
```

### 5.2 Snapshot Structure

```json
{
  "snapshot_id": "uuid",
  "skill_id": "seo-content-writer",
  "version": "2.1.0",
  "semantic_version": {
    "major": 2,
    "minor": 1,
    "patch": 0,
    "prerelease": null
  },
  "created_at": "ISO8601",
  "created_by": "evolution_engine | human_approval",
  "parent_version_id": "uuid (of v2.0.0)",
  "generation_reason": "H_dimension declining, strategy generated + approved",
  "status": "draft | candidate | stable | archived",
  "reference_data": {
    "thresholds": {
      "min_word_count": 1500,
      "max_word_count": 3000,
      "required_citations": 5,
      "min_h_score": 65
    },
    "weights": {
      "S_semantic_coverage": 0.25,
      "H_human_credibility": 0.25,
      "E1_evidence_structuring": 0.20,
      "E2_ecosystem_integration": 0.15,
      "P_performance_monitoring": 0.15
    },
    "trigger_rules": [
      { "trigger": "write article", "weight": 1.0, "workflow": "WORKFLOW_D" },
      { "trigger": "GEO article", "weight": 0.9, "workflow": "WORKFLOW_D" }
    ],
    "platform_config": {
      "chatgpt": { "min_word_count": 1500, "max_word_count": 2500 },
      "perplexity": { "freshness_days": 30 }
    },
    "limits": {
      "max_pages_per_crawl": 50,
      "max_concurrent_skills": 5,
      "skill_timeout_ms": 60000
    }
  },
  "baseline_metrics": {
    "avg_gem_score": 68.5,
    "avg_execution_time_ms": 8420,
    "success_rate": 0.94
  },
  "provenance": {
    "created_by": "strategy_generator",
    "ab_test_id": "uuid (if tested)",
    "test_result": "promoted | rejected | not_tested"
  }
}
```

### 5.3 Safety Guardrails

```
1. Always keep last 3 stable versions available for rollback
2. Major version changes (X.0.0) require human approval
3. Auto-rollback triggers:
   - z-score < -3.0 on GEM score
   - Error rate > 2x baseline
   - p95 latency > 2x baseline
4. Parity audit is a gate: new versions cannot be promoted without passing parity check
```

---

## Part 6: Parity Audit

### 6.1 Five Parity Checks

| Check | What It Verifies | Pass Threshold |
|---|---|---|
| **Trigger Coverage** | All original trigger phrases still route correctly | 100% coverage |
| **Reference Completeness** | All reference data fields are present | 100% fields |
| **Output Structure** | Output schema is unchanged | 100% compatibility |
| **Scoring Parity** | Score calculation produces same results | ±1% tolerance |
| **Capability Parity** | Same categories of findings detected | Same category count |

### 6.2 Parity Audit Output

```json
{
  "audit_id": "uuid",
  "timestamp": "ISO8601",
  "versions_compared": {
    "from": "v2.0.0",
    "to": "v2.1.0"
  },
  "results": {
    "trigger_coverage": {
      "status": "PASS | FAIL",
      "coverage": 0.98,
      "missing_triggers": []
    },
    "reference_completeness": {
      "status": "PASS | FAIL",
      "completeness": 1.0,
      "missing_fields": []
    },
    "output_structure": {
      "status": "PASS | FAIL",
      "compatible": true,
      "changed_fields": []
    },
    "scoring_parity": {
      "status": "PASS | FAIL",
      "avg_difference_pct": 0.3,
      "max_difference_pct": 0.8
    },
    "capability_parity": {
      "status": "PASS | FAIL",
      "from_categories": ["technical", "content", "schema", "geo"],
      "to_categories": ["technical", "content", "schema", "geo"],
      "missing_categories": []
    }
  },
  "overall_status": "PASS | FAIL",
  "can_promote": true,
  "blocking_issues": []
}
```

---

## Part 7: Execution Modes

### 7.1 Manual Trigger

```
/seo-geo-evolution-engine evolve
```

Runs full evolution cycle: Collect → Pattern Recognition → Strategy Generation → (if approved) A/B Test

### 7.2 Scheduled Trigger

```
Daily at 03:00 UTC (via cron/agent)
```

Runs Pattern Recognition only; generates strategies if degradation detected.

### 7.3 Post-Workflow Trigger

```
Automatically triggered after every Workflow A execution
```

Reads latest metrics, updates trend analysis.

### 7.4 Parity Check Only

```
/seo-geo-evolution-engine parity
```

Runs only the 5 parity checks, outputs report without generating strategies.

---

## Part 8: Report Templates

### 8.1 Evolution Report

```
# SEO/GEO Evolution Report

**Date:** [ISO8601]
**Window:** [24h | 7d | 30d]

## SHEEP Score Trends

| Dimension | Current | 7d Avg | 30d Avg | Change | Status |
|---|---|---|---|---|---|
| S | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |
| H | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |
| E1 | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |
| E2 | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |
| P | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |
| **GEM** | [X] | [X] | [X] | [+/-X%] | [OK/WARNING/CRITICAL] |

## Degradation Alerts

- [List of active degradation alerts]

## Active A/B Tests

| Test ID | Strategy | Variant | Sample | GEM | Status |
|---|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] | [...] |

## Proposed Strategies

| Strategy ID | Type | Target Skill | Expected Boost | Status |
|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] |

## Parity Audit Summary

- Skills audited: [N]
- Passed: [N]
- Failed: [N]

## Recommendations

1. [Priority action]
2. [Secondary action]
```

---

## Part 9: Version & Maintenance

```
Version: 1.0.0
Created: 2026-04-03
Last Updated: 2026-04-03

Change Log:
- 1.0.0: Initial release with Effect Collector, Pattern Recognizer,
         Strategy Generator, A/B Testing, Snapshot Versioning, Parity Audit

Dependencies:
- seo-geo-master-orchestrator (metrics source)
- geo_optimizer.py (SHEEP scoring)
- evolution-metrics/ (metrics storage)
- skills-snapshots/ (version storage)

Configuration:
- Default thresholds inlined in this file
- Platform-specific config: platforms.json
- Skill registry: SKILLS-REGISTRY.json

Automation:
- Scheduled evolution: daily 03:00 UTC
- Auto-rollback: z-score < -3.0
- Major version approval: human required
- Parity gate: all 5 checks must pass to promote
```
