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

→ 完整字段定义和示例见 `seekr-evolve/references/metric-schema.json`

---

## Pattern Recognizer

### Degradation Detector

```
Trigger: z-score < -2.0 for 24h window → log alert, queue for analysis
Formula: z = (current_avg - historical_avg) / historical_stddev
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
7-day avg < 30-day avg - 10% → flag declining
Declining 3+ consecutive days → trigger strategy generation
```

---

## Strategy Generator

### Strategy Types

| Type | When to Use |
|---|---|
| **Threshold Adjustment** | Reference data drift |
| **Trigger Refinement** | Trigger effectiveness dropped |
| **SHEEP Weight Reallocation** | One dim consistently drags GEM |
| **Fallback Enhancement** | error_count elevated |
| **Content Strategy** | H, E1 consistently low |

### SHEEP → Action Mapping

```
H declining → "Add author credential checks" (HIGH, +3-5 GEM)
E1 declining → "Strengthen FAQ Schema generation" (HIGH, +2-4 GEM)
S declining → "Increase keyword density targets" (MEDIUM, +2-3 GEM)
```

---

## A/B Testing Framework

### Test Configuration

```
traffic_split: 90/10 (control/candidate) | min_sample: 500/variant
max_duration: 14d | significance: p < 0.05 | metric: gem_score
```

### Test Lifecycle

```
CREATE → RUNNING (traffic split) → MONITOR (check sig every 4h)
→ STOP: promote winner | rollback loser | manual review if timeout
→ Auto-rollback on catastrophic drop (z-score < -3.0)
```

---

## Snapshot Versioning

### Version Lifecycle

```
draft → candidate → stable → archived (promoted by A/B test)
```

### Safety Guardrails

```
- Keep last 3 stable versions for rollback
- Major versions (X.0.0) require human approval
- Auto-rollback: z-score < -3.0 OR error rate > 2x baseline
- Parity audit is a gate: must pass to promote
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

→ 使用 `seekr-evolve/references/report-template.md` 作为进化报告模板

---

## Example Usage

```
用户: 运行SeekR进化周期

Claude: SeekR Evolution Engine...
1. 收集指标 (24h) → GEM z-score: -1.2 (正常), E1: -3.2% (略降)
2. 策略: 调整E1权重+2%, 添加FAQ Schema频率
3. A/B测试: 2进行中 | 快照: v1.2.0 stable

GEM: 71.5 | E1: 65↓ | Parity: 12/12 PASS
Recommendations: [HIGH] 提升E1维度, [MEDIUM] 调整关键词密度目标
```
