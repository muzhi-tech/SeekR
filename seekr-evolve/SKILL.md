---
name: seekr-evolve
version: "1.0.0"
description: |
  Self-evolution engine for SeekR SEO/GEO skills. Monitors skill execution metrics (SHEEP/GEM scores),
  detects performance degradation patterns, generates optimization strategies, and validates them
  via A/B testing before promotion. Consumes metrics from SeekR execution logs.
  Triggers: "evolve", "optimize skills", "check skill health", "run parity audit", "trigger evolution".
license: CC BY-NC-SA 4.0
compatibility: "Claude Code ≥1.0"
metadata:
  author: muzhi-tech
  geo-relevance: high
  tags:
    - evolution
    - skill-optimization
    - metrics
    - ab-testing
    - self-improving
    - seo
    - geo
triggers:
  - "evolve"
  - "optimize skills"
  - "check skill health"
  - "run parity audit"
  - "trigger evolution"
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# SeekR Evolution Engine

## Purpose

The Evolution Engine is the **meta-layer** that makes the SeekR SEO/GEO skill system self-improving:
1. Consumes execution metrics from SeekR orchestrator
2. Detects performance degradation via Pattern Recognition
3. Generates optimization strategies
4. Validates strategies via A/B Testing
5. Promotes winning versions via Snapshot Versioning
6. Runs Parity Audits to prevent capability regression

**Silent execution protocol — never ask, never stop, always complete.**

## Effect Collector

### Data Collection Sources

```
Sources:
1. evolution-metrics/<execution_id>.json (from SeekR orchestrator)
   → Every workflow execution produces this file

2. Manual trigger (via this skill)
   → /seekr-evolve evolve

3. Scheduled trigger (daily at 03:00 UTC)
   → Automated evolution cycle
```

### Metrics Collected per Execution

```json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | WORKFLOW_D",
  "skill_name": "string",
  "skill_version": "semver",
  "sheep_scores": {
    "S_semantic_coverage": { "raw": 0-100, "weight": 0.25 },
    "H_human_credibility": { "raw": 0-100, "weight": 0.25 },
    "E1_evidence_structuring": { "raw": 0-100, "weight": 0.20 },
    "E2_ecosystem_integration": { "raw": 0-100, "weight": 0.15 },
    "P_performance_monitoring": { "raw": 0-100, "weight": 0.15 }
  },
  "gem_score": 0-100,
  "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "duration_ms": 0,
  "error_count": 0
}
```

---

## Pattern Recognizer

### Degradation Detector (z-score method)

```
Trigger: z-score < -2.0 for 24h window
Action: Log degradation alert, queue for analysis

z-score formula:
  z = (current_avg - historical_avg) / historical_stddev
```

### SHEEP Dimension Thresholds

| Dimension | Critical | Warning |
|---|---|---|
| S_semantic_coverage | < 55 | < 65 |
| H_human_credibility | < 50 | < 60 |
| E1_evidence_structuring | < 45 | < 55 |
| E2_ecosystem_integration | < 40 | < 50 |
| P_performance_monitoring | < 45 | < 55 |

### Trend Analysis

```
Per dimension:
  1. Calculate 7-day moving average
  2. Calculate 30-day moving average
  3. If 7-day avg < 30-day avg - 10%: flag as declining
  4. If declining for 3+ consecutive days: trigger strategy generation
```

---

## Strategy Generator

### Strategy Types

| Type | Description | When to Use |
|---|---|---|
| **Threshold Adjustment** | Adjust scoring thresholds | Reference data drift |
| **Trigger Refinement** | Update trigger weights | Trigger effectiveness dropped |
| **SHEEP Weight Reallocation** | Shift weight to low-scoring dims | One dim consistently drags GEM |
| **Fallback Enhancement** | Improve error handling | error_count elevated |
| **Content Strategy** | Recommend focus for Workflow D | H, E1 consistently low |

### SHEEP → Action Mapping

```
H_human_credibility declining:
  → Strategy: "Add author credential checks"
  → Priority: HIGH
  → Expected GEM boost: +3-5 points

E1_evidence_structuring declining:
  → Strategy: "Strengthen FAQ Schema generation"
  → Priority: HIGH
  → Expected GEM boost: +2-4 points

S_semantic_coverage declining:
  → Strategy: "Increase keyword density targets"
  → Priority: MEDIUM
  → Expected GEM boost: +2-3 points
```

---

## A/B Testing Framework

### Test Configuration

```
Default test configuration:
  - traffic_split: 90% control / 10% candidate
  - minimum_sample_size: 500 per variant
  - maximum_duration_days: 14
  - significance_level: 0.95 (p < 0.05)
  - early_stop_threshold: 0.99
  - test_metric: gem_score (primary)
```

### Test Lifecycle

```
1. CREATE: Strategy approved → create A/B test
2. RUNNING: Traffic split, metrics collected
3. MONITOR: Check significance every 4h
4. STOP:
   - Significance reached → promote winner
   - Loser detected → stop and rollback
   - Duration exceeded → manual review
   - Catastrophic drop (z-score < -3.0) → auto-rollback
5. REPORT: Generate test report
```

---

## Snapshot Versioning

### Version Lifecycle

```
draft → candidate → stable → archived
                      ↑
              promoted by A/B test
```

### Safety Guardrails

```
1. Always keep last 3 stable versions for rollback
2. Major version changes (X.0.0) require human approval
3. Auto-rollback triggers:
   - z-score < -3.0 on GEM score
   - Error rate > 2x baseline
4. Parity audit is a gate: must pass to promote
```

---

## Parity Audit

### Five Parity Checks

| Check | What It Verifies | Pass Threshold |
|---|---|---|
| **Trigger Coverage** | All trigger phrases route correctly | 100% coverage |
| **Reference Completeness** | All reference data fields present | 100% fields |
| **Output Structure** | Output schema unchanged | 100% compatibility |
| **Scoring Parity** | Score calculation produces same results | ±1% tolerance |
| **Capability Parity** | Same categories of findings detected | Same category count |

---

## Execution Modes

### Manual Trigger
```
/seekr-evolve evolve
```
Runs full evolution cycle: Collect → Pattern Recognition → Strategy Generation → A/B Test

### Scheduled Trigger
```
Daily at 03:00 UTC
```
Runs Pattern Recognition only

### Parity Check Only
```
/seekr-evolve parity
```
Runs only the 5 parity checks

---

## Evolution Report Template

```
# SeekR Evolution Report

**Date:** [ISO8601]
**Window:** [24h | 7d | 30d]

## SHEEP Score Trends

| Dim | Current | 7d Avg | 30d Avg | Change | Status |
|---|---|---|---|---|---|
| S | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |
| H | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |
| E1 | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |
| E2 | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |
| P | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |
| **GEM** | [X] | [X] | [X] | [+/-X%] | [OK/WARN/CRIT] |

## Degradation Alerts

- [List of active alerts]

## Active A/B Tests

| Test ID | Strategy | Variant | Sample | GEM | Status |
|---|---|---|---|---|---|

## Proposed Strategies

| Strategy ID | Type | Expected Boost | Status |
|---|---|---|---|

## Parity Audit Summary

- Skills audited: [N]
- Passed: [N]
- Failed: [N]

## Recommendations

1. [Priority action]
2. [Secondary action]
```

---

## Example Usage

```
用户: 运行SeekR进化周期

Claude: 启动SeekR Evolution Engine...

1. 收集执行指标 (last 24h)...
2. 执行模式识别...
   - GEM z-score: -1.2 (正常范围)
   - SHEEP趋势: E1略微下降 (-3.2%)
3. 生成优化策略...
   - 策略#1: 建议调整E1权重 +2%
   - 策略#2: 添加FAQ Schema生成频率
4. A/B测试状态: 2个进行中
5. 快照版本: v1.2.0 stable

═══════════════════════════════════════
  SeekR Evolution Report
  Window: 24h | Date: 2026-04-03
═══════════════════════════════════════

GEM: 71.5 | Status: OK
S: 74 | H: 68 | E1: 65↓ | E2: 72 | P: 78

Degradation Alerts: None
Active A/B Tests: 2
Proposed Strategies: 2
Parity: 12/12 PASS

Recommendations:
1. [HIGH] 提升E1维度 - FAQ Schema加强
2. [MEDIUM] 调整关键词密度目标
```
