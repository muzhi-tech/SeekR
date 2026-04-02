# SEO/GEO Skill Evolution Engine - Architecture Design

---

## 0. clawd-code 源代码级进化机制分析

### 0.1 调查范围与方法

针对 Boss geoclaw 坚持认为 https://github.com/godfalcon/clawd-code 包含真正自我进化机制的质疑，本节对该仓库进行了彻底的源代码级调查。

**调查的文件范围：**
- 核心 Python 文件：`parity_audit.py`, `runtime.py`, `tools.py`, `models.py`, `commands.py`, `cost_tracker.py`, `history.py`, `query_engine.py`, `task.py`, `tasks.py`, `context.py`, `setup.py`, `port_manifest.py`, `main.py`, `ink.py`, `query.py`
- 目录：`skills/`, `hooks/`, `state/`, `coordinator/`, `bootstrap/`, `services/`, `plugins/`, `memdir/`, `constants/`, `bridge/`, `buddy/`, `reference_data/`
- 参考数据：`reference_data/subsystems/*.json`, `tools_snapshot.json`, `commands_snapshot.json`
- GitHub 关键词搜索：`evolve`, `learn`, `optimize`, `feedback` (0 结果)

### 0.2 发现的三个基础模式

#### 模式 1: Prompt Routing (runtime.py)

```python
class PortRuntime:
    def route_prompt(self, prompt: str, limit: int = 5) -> list[RoutedMatch]:
        tokens = {token.lower() for token in prompt.replace('/', ' ').replace('-', ' ').split() if token}
        by_kind = {
            'command': self._collect_matches(tokens, PORTED_COMMANDS, 'command'),
            'tool': self._collect_matches(tokens, PORTED_TOOLS, 'tool'),
        }
        # ... 简单的 token 匹配路由逻辑
```

**分析：** 这是一个基于 token 匹配的简单路由机制，按 `/` 和 `-` 分词后与预定义的 PORTED_COMMANDS 和 PORTED_TOOLS 进行匹配。没有学习、没有权重调整、没有基于历史执行的优化。

#### 模式 2: Reference Data Snapshots (reference_data/)

```
src/reference_data/
├── commands_snapshot.json    # 命令条目快照
├── tools_snapshot.json       # 工具条目快照
├── archive_surface_snapshot.json
└── subsystems/              # 29 个子系统元数据
    ├── skills.json           # skills 包 (20 模块)
    ├── coordinator.json
    ├── assistant.json
    └── ...
```

**分析：** 所有快照都是静态 JSON 文件，由 `load_tool_snapshot()` 和 `load_command_snapshot()` 加载到内存中。快照在加载后不会更新，不存在基于执行结果的动态修改。

#### 模式 3: Parity Audit (parity_audit.py)

```python
def run_parity_audit() -> ParityAuditResult:
    current_entries = {path.name for path in CURRENT_ROOT.iterdir()}
    root_hits = [target for target in ARCHIVE_ROOT_FILES.values() if target in current_entries]
    # ... 计算覆盖率指标
    return ParityAuditResult(
        archive_present=ARCHIVE_ROOT.exists(),
        root_file_coverage=(len(root_hits), len(ARCHIVE_ROOT_FILES)),
        # ...
    )
```

**分析：** Parity Audit 仅用于衡量 Python 移植工作区与原始 TypeScript 快照之间的覆盖率差距。它是一个静态分析工具，不是进化机制。

### 0.3 代码层面的进化机制缺失

| 可能的进化机制 | 是否存在 | 证据 |
|-------------|---------|------|
| 基于执行结果修改自身行为 | **不存在** | `cost_tracker.py` 仅记录，无反馈逻辑 |
| 基于历史学习调整路由 | **不存在** | `runtime.py` 的 `_score()` 仅基于静态 token 匹配 |
| 参数自动优化 | **不存在** | 无任何参数调优代码 |
| 版本自动演进 | **不存在** | `SkillVersion` 数据类仅定义结构，无自动更新逻辑 |
| A/B 测试框架 | **不存在** | 无任何 A/B 测试相关代码 |
| 效果指标收集与分析 | **不存在** | `history.py` 仅记录事件标题和详情，无指标分析 |
| 模式识别与策略生成 | **不存在** | 无任何模式识别算法 |
| 反馈闭环 | **不存在** | 无任何从指标到行为调整的路径 |

### 0.4 关键代码证据

**cost_tracker.py (成本追踪) — 无进化逻辑：**
```python
@dataclass
class CostTracker:
    total_units: int = 0
    events: list[str] = field(default_factory=list)

    def record(self, label: str, units: int) -> None:
        self.total_units += units
        self.events.append(f'{label}:{units}')
        # 仅记录，无任何分析或调整逻辑
```

**history.py (历史记录) — 无学习机制：**
```python
@dataclass
class HistoryEvent:
    title: str
    detail: str

@dataclass
class HistoryLog:
    events: list[HistoryEvent] = field(default_factory=list)

    def add(self, title: str, detail: str) -> None:
        self.events.append(HistoryEvent(title=title, detail=detail))
        # 仅追加，无任何基于历史的学习或调整
```

**skills.json (技能元数据) — 静态快照：**
```json
{
  "archive_name": "skills",
  "package_name": "skills",
  "module_count": 20,
  "sample_files": [
    "skills/bundled/loop.ts",
    "skills/bundled/simplify.ts",
    "skills/bundled/verify.ts"
    // ... 共 20 个模块
  ]
}
```
虽然文件名暗示有 `loop`, `simplify`, `verify` 等功能，但这些只是静态元数据，不包含实际执行逻辑。

### 0.5 结论

**clawd-code 仓库确实不包含任何自我进化机制。**

该仓库的三个所谓"模式"都是**静态的、无反馈的机制**：
1. **Prompt Routing** — 基于 token 的静态路由，不学习
2. **Reference Data Snapshots** — 静态 JSON 快照，不更新
3. **Parity Audit** — 覆盖率审计工具，不调整行为

没有任何代码实现了：
- 基于执行效果的自我修改
- 基于历史数据的模式学习
- 基于指标变化的参数优化
- 任何形式的 A/B 测试或实验框架
- 任何从指标到行为的反馈闭环

### 0.6 对 Evolution Engine 设计的影响

clawd-code 仓库仅提供了**静态基础设施**，但缺少进化的**核心机制**：
- 它有数据模型 (`models.py`) 但没有行为模型
- 它有追踪 (`cost_tracker.py`, `history.py`) 但没有分析
- 它有路由 (`runtime.py`) 但没有优化
- 它有版本快照 (`reference_data/`) 但没有版本演进

**Evolution Engine 需要从头构建这些缺失的机制。**

---

## 1. 概述

### 1.1 设计目标

传统的 Prompt Routing、Reference Data Snapshots、Parity Audit 模式解决了静态路由和版本管理问题，但缺乏**自我优化能力**。Evolution Engine 构建了一个闭环的、可自我进化的 Skill 优化系统。

### 1.2 核心愿景

```
┌─────────────────────────────────────────────────────────────────┐
│                        Evolution Engine                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Metrics   │───▶│  Pattern    │───▶│  Strategy   │         │
│  │  Collector  │    │ Recognizer  │    │  Generator  │         │
│  └─────────────┘    └─────────────┘    └──────┬──────┘         │
│         ▲                                       │                │
│         │            ┌─────────────────────────┘                │
│         │            ▼                                           │
│         │     ┌─────────────┐    ┌─────────────┐                │
│         └─────│ Feedback    │◀───│    A/B      │                │
│               │   Loop      │    │   Testing   │                │
│               └─────────────┘    └─────────────┘                │
└─────────────────────────────────────────────────────────────────┘
         ▲
         │ 观察/反馈
┌────────┴────────┐
│   Other Skills  │
│ (seo, geo, etc) │
└─────────────────┘
```

---

## 2. 核心数据模型

### 2.1 JSON Schema 定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "definitions": {

    "SkillVersion": {
      "type": "object",
      "required": ["versionId", "skillId", "parameters", "createdAt", "status"],
      "properties": {
        "versionId": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9-_]+$"
        },
        "skillId": {
          "type": "string",
          "description": "关联的 Skill 标识符，如 'seo-content', 'geo-llmstxt'"
        },
        "parentVersionId": {
          "type": ["string", "null"],
          "description": "父版本，用于追溯进化链"
        },
        "parameters": {
          "type": "object",
          "description": "该版本的配置参数"
        },
        "promptTemplate": {
          "type": "string",
          "description": "使用的提示词模板"
        },
        "createdAt": {
          "type": "string",
          "format": "date-time"
        },
        "status": {
          "type": "string",
          "enum": ["active", "archived", "promoted", "rejected"]
        },
        "executionCount": {
          "type": "integer",
          "minimum": 0,
          "default": 0
        }
      }
    },

    "EffectMetric": {
      "type": "object",
      "required": ["metricId", "skillVersionId", "timestamp", "metricType", "value"],
      "properties": {
        "metricId": {
          "type": "string"
        },
        "skillVersionId": {
          "type": "string"
        },
        "sessionId": {
          "type": "string",
          "description": "执行会话ID，用于关联同一轮交互的所有指标"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "metricType": {
          "type": "string",
          "enum": [
            "ranking_improvement",    // 搜索排名提升
            "traffic_change",         // 流量变化
            "ai_visibility",          // AI 可见度 (SGE/AIO)
            "citation_rate",          // 引用率
            "click_through_rate",     // 点击率
            "bounce_rate",            // 跳出率
            "dwell_time",            // 停留时间
            "conversion_rate",       // 转化率
            "latency_ms",            // 响应延迟
            "token_cost",            // Token 消耗
            "error_rate",            // 错误率
            "user_satisfaction"      // 用户满意度
          ]
        },
        "value": {
          "type": "number",
          "description": "指标值"
        },
        "previousValue": {
          "type": "number",
          "description": "变化前的值，用于计算 delta"
        },
        "delta": {
          "type": "number",
          "description": "变化量 (value - previousValue)"
        },
        "deltaPercent": {
          "type": "number",
          "description": "变化百分比"
        },
        "dimensions": {
          "type": "object",
          "description": "细分维度",
          "properties": {
            "keyword": { "type": "string" },
            "page": { "type": "string" },
            "searchEngine": { "type": "string", "enum": ["google", "bing", "baidu", "yandex"] },
            "region": { "type": "string" },
            "device": { "type": "string", "enum": ["desktop", "mobile", "tablet"] },
            "intent_type": { "type": "string", "enum": ["informational", "navigational", "transactional", "commercial"] }
          }
        },
        "dataSource": {
          "type": "string",
          "enum": ["google_search_console", "ga4", "semrush", "ahrefs", "position_tracker", "ai_analytics", "manual"]
        }
      }
    },

    "ABTest": {
      "type": "object",
      "required": ["testId", "name", "status", "variants", "startTime"],
      "properties": {
        "testId": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "status": {
          "type": "string",
          "enum": ["draft", "running", "paused", "completed", "cancelled"]
        },
        "variants": {
          "type": "array",
          "minItems": 2,
          "items": {
            "type": "object",
            "required": ["variantId", "versionId", "trafficPercentage"],
            "properties": {
              "variantId": {
                "type": "string",
                "enum": ["control", "variant_a", "variant_b", "variant_c"]
              },
              "versionId": {
                "type": "string"
              },
              "trafficPercentage": {
                "type": "number",
                "minimum": 0,
                "maximum": 100
              },
              "metrics": {
                "type": "object",
                "additionalProperties": { "type": "number" }
              },
              "sampleSize": {
                "type": "integer"
              }
            }
          }
        },
        "startTime": {
          "type": "string",
          "format": "date-time"
        },
        "endTime": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "minimumSampleSize": {
          "type": "integer",
          "description": "最小样本量"
        },
        "statisticalSignificance": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "default": 0.95
        },
        "primaryMetric": {
          "type": "string"
        },
        "winner": {
          "type": ["string", "null"],
          "description": "胜出版本ID"
        },
        "confidenceInterval": {
          "type": "object",
          "properties": {
            "lower": { "type": "number" },
            "upper": { "type": "number" },
            "confidence": { "type": "number" }
          }
        }
      }
    },

    "EvolutionStrategy": {
      "type": "object",
      "required": ["strategyId", "createdAt", "status"],
      "properties": {
        "strategyId": {
          "type": "string"
        },
        "triggerType": {
          "type": "string",
          "enum": ["degradation_detected", "opportunity_identified", "manual_trigger", "scheduled", "ab_test_completed"]
        },
        "targetSkillId": {
          "type": "string"
        },
        "sourceVersionId": {
          "type": "string"
        },
        "proposedChanges": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "parameter": { "type": "string" },
              "currentValue": {},
              "proposedValue": {},
              "changeType": {
                "type": "string",
                "enum": ["replace", "increment", "decrement", "restructure"]
              },
              "rationale": { "type": "string" }
            }
          }
        },
        "expectedImpact": {
          "type": "object",
          "properties": {
            "metricType": { "type": "string" },
            "expectedDelta": { "type": "number" },
            "expectedDeltaPercent": { "type": "number" },
            "confidence": { "type": "number" }
          }
        },
        "createdAt": {
          "type": "string",
          "format": "date-time"
        },
        "status": {
          "type": "string",
          "enum": ["proposed", "approved", "rejected", "implemented", "rolled_back"]
        },
        "abTestId": {
          "type": ["string", "null"]
        },
        "implementationNotes": {
          "type": "string"
        }
      }
    },

    "SkillEvolutionRecord": {
      "type": "object",
      "required": ["recordId", "skillId", "versionHistory"],
      "properties": {
        "recordId": {
          "type": "string"
        },
        "skillId": {
          "type": "string"
        },
        "createdAt": {
          "type": "string",
          "format": "date-time"
        },
        "updatedAt": {
          "type": "string",
          "format": "date-time"
        },
        "versionHistory": {
          "type": "array",
          "items": { "$ref": "#/definitions/SkillVersion" }
        },
        "currentActiveVersionId": {
          "type": "string"
        },
        "lifetimeMetrics": {
          "type": "object",
          "additionalProperties": { "type": "number" }
        },
        "evolutionCount": {
          "type": "integer"
        },
        "lastEvolutionAt": {
          "type": ["string", "null"],
          "format": "date-time"
        }
      }
    },

    "EvolutionSnapshot": {
      "type": "object",
      "required": ["snapshotId", "timestamp", "allRecords"],
      "properties": {
        "snapshotId": {
          "type": "string"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "allRecords": {
          "type": "array",
          "items": { "$ref": "#/definitions/SkillEvolutionRecord" }
        },
        "topPerformers": {
          "type": "array",
          "description": "各指标维度表现最佳的版本"
        },
        "needsAttention": {
          "type": "array",
          "description": "需要关注的技能列表"
        }
      }
    }
  }
}
```

### 2.2 效果指标体系详解

| 指标类型 | 收集频率 | 数据来源 | 权重 |
|---------|---------|---------|-----|
| ranking_improvement | 每日/每周 | Search Console, SEMrush, Ahrefs | 0.25 |
| traffic_change | 每日 | Google Analytics 4 | 0.20 |
| ai_visibility | 每周 | SGE/AIO Tracker, SerpAPI | 0.20 |
| citation_rate | 每周 | Backlink 工具 | 0.10 |
| click_through_rate | 每日 | Search Console | 0.10 |
| conversion_rate | 每周 | Analytics, CRM | 0.10 |
| latency_ms | 每次执行 | 系统埋点 | 0.05 |
| token_cost | 每次执行 | 系统埋点 | 0.05 |
| user_satisfaction | 每季度 | 用户调研 | 0.05 |

---

## 3. Evolution Engine 组件设计

### 3.1 效果收集器 (Metrics Collector)

```
输入 ─────────────────────────────────────────────────────────────────▶
├── Skill 执行事件 (每次 Skill 被调用时触发)
│   ├── skill_id, version_id, session_id
│   ├── input_parameters, output_result
│   ├── execution_time_ms, token_usage
│   └── error_occurred (boolean)
│
├── 外部数据拉取 (定时任务)
│   ├── Google Search Console API (排名、CTR、展示量)
│   ├── Google Analytics 4 API (流量、转化、跳出率)
│   ├── SEO 工具 API (SEMrush, Ahrefs, Moz)
│   └── AI 可见度工具 (SGE Tracker, AIO Monitor)
│
└── 用户反馈 (可选)
    ├── thumbs_up/down
    ├── star_rating (1-5)
    └── text_feedback
```

```
输出 ─────────────────────────────────────────────────────────────────▶
├── EffectMetric 数组 (存入 Metrics Store)
├── 实时告警 (当指标异常时)
│   └── { type: "degradation", metric: "ranking_improvement", delta: -15% }
└── Dashboard 聚合数据
```

**关键算法逻辑:**

```typescript
interface MetricsCollector {
  // 实时事件处理
  onSkillExecution(event: SkillExecutionEvent): void;

  // 批量数据拉取 (Cron: 每日/每周)
  fetchExternalMetrics(dateRange: DateRange): Promise<EffectMetric[]>;

  // 指标聚合计算
  aggregateMetrics(
    skillId: string,
    versionId: string,
    timeWindow: TimeWindow
  ): AggregatedMetrics;

  // 异常检测
  detectAnomalies(
    current: AggregatedMetrics,
    historical: AggregatedMetrics[]
  ): AnomalyAlert[];
}

interface AnomalyAlert {
  severity: "info" | "warning" | "critical";
  metricType: string;
  currentValue: number;
  expectedRange: { min: number; max: number };
  deviationPercent: number;
  suggestedAction: string;
}
```

**触发条件:**
- **实时**: 每次 Skill 执行完成
- **定时**: 每日 02:00 UTC (搜索数据), 每小时 (流量数据)
- **手动**: API 调用触发

---

### 3.2 模式识别器 (Pattern Recognizer)

```
输入 ─────────────────────────────────────────────────────────────────▶
├── 时间序列指标数据
│   └── metrics: EffectMetric[] (通常取 7/30/90 天数据)
│
├── 版本变更历史
│   └── versionChanges: Array<{ before: Version, after: Version, changeTime: Date }>
│
└── 外部上下文
    └── searchAlgorithmUpdates: AlgorithmUpdate[]
    └── competitorMovements: CompetitorMove[]
```

```
输出 ─────────────────────────────────────────────────────────────────▶
├── PatternReport
│   ├── trendAnalysis: Trend[]
│   │   └── { metricType, direction, slope, confidence }
│   │
│   ├── correlationFindings: Correlation[]
│   │   └── { metricA, metricB, correlationCoefficient, pValue }
│   │
│   ├── causalHypotheses: Hypothesis[]
│   │   └── { cause, effect, confidence, supportingEvidence }
│   │
│   ├── seasonalityDetected: SeasonalityPattern[]
│   │   └── { metric, period, amplitude, phase }
│   │
│   └── evolutionRecommendation: Recommendation
│       └── { shouldEvolve: boolean, priority: "low"|"medium"|"high", reason: string }
```

**关键算法逻辑:**

```typescript
interface PatternRecognizer {
  // 趋势检测 (线性回归/移动平均)
  detectTrends(
    timeSeries: TimeSeriesPoint[],
    confidenceThreshold: number
  ): Trend[];

  // 相关性分析 (Pearson/Spearman)
  findCorrelations(
    metricsA: TimeSeriesPoint[],
    metricsB: TimeSeriesPoint[]
  ): Correlation[];

  // 因果推断 (Granger Causality Test)
  inferCausality(
    potentialCauses: TimeSeriesPoint[],
    effect: TimeSeriesPoint[]
  ): Hypothesis[];

  // 季节性检测 (STL 分解/Fourier)
  detectSeasonality(
    timeSeries: TimeSeriesPoint[],
    expectedPeriods: number[]
  ): SeasonalityPattern[];

  // 参数敏感性分析
  analyzeParameterSensitivity(
    versionHistory: SkillVersion[],
    metricsHistory: EffectMetric[]
  ): ParameterImpact[];

  // 生成进化建议
  generateEvolutionRecommendation(
    allAnalyses: PatternReport
  ): EvolutionRecommendation;
}

// 核心算法: 参数敏感性分析
interface ParameterImpact {
  parameterName: string;
  impactScore: number;        // -1 to 1
  affectedMetrics: string[];
  optimalRange: { min: any; max: any };
  confidence: number;
  interactionWith: string[];  // 哪些参数有交互作用
}
```

**触发条件:**
- 每日凌晨 03:00 UTC 运行全量分析
- 当指标异常告警时触发针对性分析
- 手动触发

---

### 3.3 策略生成器 (Strategy Generator)

```
输入 ─────────────────────────────────────────────────────────────────▶
├── EvolutionRecommendation (从 PatternRecognizer)
│   └── { shouldEvolve, priority, reason, suggestedFocus }
│
├── ParameterImpact[] (从 PatternRecognizer)
│   └── 高敏感性参数及其最优范围
│
├── 当前活跃版本 (从 Skill Registry)
│   └── { versionId, parameters, promptTemplate }
│
└── 进化目标约束
    └── { maxTokenCostIncrease: 20%, maxLatencyIncrease: 50ms }
```

```
输出 ─────────────────────────────────────────────────────────────────▶
├── EvolutionStrategy[]
│   └── 每个策略包含:
│       ├── 具体的参数变更方案
│       ├── 变更的优先级排序
│       ├── 预期的指标影响
│       ├── 风险评估
│       └── 回滚计划
│
└── 候选版本提案 (Candidate Versions)
    └── 为 A/B 测试生成多个变体
```

**关键算法逻辑:**

```typescript
interface StrategyGenerator {
  // 基于参数敏感性生成候选策略
  generateCandidateStrategies(
    currentVersion: SkillVersion,
    paramImpacts: ParameterImpact[],
    constraint: EvolutionConstraint
  ): EvolutionStrategy[];

  // 提示词优化策略 (Prompt Engineering)
  generatePromptStrategies(
    currentPrompt: string,
    performanceIssue: string,
    goalMetrics: MetricTarget[]
  ): PromptStrategy[];

  // 策略风险评估
  assessStrategyRisk(
    strategy: EvolutionStrategy,
    historicalData: SkillEvolutionRecord
  ): RiskAssessment;

  // 选择最优策略
  selectOptimalStrategy(
    candidates: EvolutionStrategy[],
    objectives: OptimizationObjective
  ): EvolutionStrategy;

  // 生成回滚计划
  generateRollbackPlan(
    strategy: EvolutionStrategy,
    currentVersion: SkillVersion
  ): RollbackPlan;
}

interface RiskAssessment {
  overallRisk: "low" | "medium" | "high";
  riskFactors: {
    factor: string;
    probability: number;
    impact: number;
  }[];
  mitigationStrategies: string[];
  expectedSuccessRate: number;
}

interface OptimizationObjective {
  primaryMetric: string;      // 主要优化指标
  secondaryMetrics: string[];
  acceptableTradeoffs: {
    metricA: string;
    metricB: string;
    maxAcceptableDegradation: number;
  }[];
}
```

**策略生成算法:**

```python
# 伪代码: 策略生成
def generate_evolution_strategies(skill, param_impacts, constraints):
    strategies = []

    # 1. 单参数优化 (聚焦高敏感性参数)
    for param in sorted(param_impacts, key=lambda p: abs(p.impact_score), reverse=True):
        if abs(param.impact_score) > THRESHOLD (0.3):
            strategies.extend(
                nudge_parameter(skill, param, direction="positive"),
                nudge_parameter(skill, param, direction="negative"),
                set_to_optimal_range(skill, param)
            )

    # 2. 多参数组合优化
    high_impact_params = [p for p in param_impacts if abs(p.impact_score) > 0.5]
    if len(high_impact_params) >= 2:
        strategies.append(
            optimize_parameter_group(skill, high_impact_params)
        )

    # 3. 提示词重构 (当参数调优收益递减时)
    if total_param_optimization_gain < MIN_GAIN:
        strategies.append(
            restructure_prompt(skill, focus_on=identified_weaknesses)
        )

    # 4. 裁剪低效元素
    strategies.append(
        prune_low_performing_elements(skill)
    )

    return filter_by_constraints(strategies, constraints)
```

**触发条件:**
- PatternRecognizer 输出 `shouldEvolve: true` 时
- 手动触发 (运维人员/产品经理决策)
- 定时检查 (每周末生成下周策略提案)

---

### 3.4 A/B 测试框架 (A/B Testing Framework)

```
输入 ─────────────────────────────────────────────────────────────────▶
├── EvolutionStrategy[] (从 StrategyGenerator)
│   └── 候选策略列表
│
├── 流量配置
│   └── { totalSessions, allocatedSessions, minimumPerVariant }
│
├── 测试配置
│   └── { duration, significanceLevel, minimumSampleSize }
│
└── 版本代码
    └── 各个 variant 的实现
```

```
输出 ─────────────────────────────────────────────────────────────────▶
├── ABTest 实例
│   └── { testId, variants, status, startTime }
│
├── 实时监控数据
│   └── { variantId, metrics, sampleSize, confidence }
│
└── 测试结论
    └── { winner, confidence, pValue, recommendation }
```

**关键算法逻辑:**

```typescript
interface ABTestingFramework {
  // 创建 A/B 测试
  createTest(
    name: string,
    variants: Variant[],
    config: TestConfig
  ): ABTest;

  // 流量分配 (Consistent Hashing)
  assignVariant(sessionId: string, testId: string): string;

  // 收集测试数据
  recordTestEvent(
    testId: string,
    variantId: string,
    sessionId: string,
    metrics: Record<string, number>
  ): void;

  // 实时统计计算
  computeTestStatistics(testId: string): TestStatistics;

  // 显著性检验 (Z-test / T-test / Bayesian)
  checkStatisticalSignificance(
    testId: string,
    method: "frequentist" | "bayesian"
  ): SignificanceResult;

  // 提前终止判断 (基于显著性/样本量)
  shouldEarlyTerminate(testId: string): EarlyTerminationDecision;

  // 生成测试报告
  generateTestReport(testId: string): TestReport;

  // 胜出版本推广
  promoteWinner(testId: string): PromotionResult;
}

interface TestStatistics {
  variantId: string;
  sampleSize: number;
  mean: Record<string, number>;
  variance: Record<string, number>;
  confidenceInterval: Record<string, ConfidenceInterval>;
  conversionRate?: {
    rate: number;
    interval: [number, number];
  };
}

interface SignificanceResult {
  isSignificant: boolean;
  pValue: number;
  confidenceLevel: number;
  effectSize: number;
  recommendation: "continue" | "stop_winner" | "stop_loser" | " inconclusive";
}

interface EarlyTerminationDecision {
  shouldTerminate: boolean;
  reason: string;
  winningVariant?: string;
  confidenceLevel: number;
}
```

**A/B 测试配置默认值:**

```yaml
test_configuration:
  minimum_sample_size: 1000        # 每 variant 最小样本量
  maximum_duration_days: 30         # 最大测试时长
  significance_level: 0.95         # 显著性水平 (95%)
  minimum_detectable_effect: 0.05   # 最小可检测效果 (5%)
  early_stop_threshold: 0.99        # 提前停止的置信度
  traffic_allocation:
    control: 50                     # 对照组流量占比
    variants: 50                    # 所有变体流量占比总和
  bayesian_prior:
    alpha: 1                        # Beta 先验 alpha
    beta: 1                         # Beta 先验 beta
```

**流量分配算法:**

```typescript
// Consistent Hashing 保证用户一致性体验
function assignVariant(sessionId: string, testId: string, variants: string[]): string {
  const hash = crypto.createHash('sha256')
    .update(`${testId}:${sessionId}`)
    .digest('hex');

  const hashValue = parseInt(hash.substring(0, 8), 16);
  const bucket = hashValue % 100;

  // 累积分布确定 variant
  let cumulative = 0;
  for (const variant of variants) {
    cumulative += variant.trafficPercentage;
    if (bucket < cumulative) return variant.variantId;
  }

  return variants[variants.length - 1].variantId;
}
```

**触发条件:**
- StrategyGenerator 输出候选策略时自动创建
- 手动创建 (指定特定策略)
- 测试时长达到上限时自动结束

---

## 4. 自动化触发条件

### 4.1 触发事件体系

```
┌─────────────────────────────────────────────────────────────────────┐
│                        触发条件矩阵                                    │
├──────────────┬────────────────────────────────────────────────────────┤
│    阶段      │                      触发条件                          │
├──────────────┼────────────────────────────────────────────────────────┤
│  效果收集    │ • Skill 执行完成 (实时)                                 │
│              │ • 每日 02:00 UTC (Search Console 数据)                 │
│              │ • 每日 04:00 UTC (Analytics 数据)                      │
│              │ • 每周一 00:00 UTC (SEO 工具聚合数据)                   │
├──────────────┼────────────────────────────────────────────────────────┤
│  模式识别    │ • 每日 03:00 UTC (全量分析)                            │
│              │ • 效果指标异常时 (实时触发)                             │
│              │ • Algorithm Update 事件 (Google Core Update 等)        │
│              │ • 手动触发                                            │
├──────────────┼────────────────────────────────────────────────────────┤
│  策略生成    │ • PatternRecognizer 输出 shouldEvolve: true            │
│              │ • 手动触发 (产品决策)                                  │
│              │ • 每周末生成下周计划                                   │
├──────────────┼────────────────────────────────────────────────────────┤
│  A/B 测试    │ • 新策略生成时自动创建                                 │
│              │ • 手动指定策略                                         │
│              │ • 测试达最大时长                                       │
│              │ • 统计显著性达成                                       │
├──────────────┼────────────────────────────────────────────────────────┤
│  结果固化    │ • A/B 测试完成 (winner 确定)                          │
│              │ • 手动批准                                             │
│              │ • 新版本稳定运行 7 天后自动提升为 active                │
└──────────────┴────────────────────────────────────────────────────────┘
```

### 4.2 关键阈值配置

```yaml
# 效果异常检测阈值
anomaly_detection:
  ranking_improvement:
    warning_threshold: -5%    # 排名下降 5% 触发 warning
    critical_threshold: -15%  # 排名下降 15% 触发 critical
  ai_visibility:
    warning_threshold: -10%
    critical_threshold: -25%
  traffic_change:
    warning_threshold: -8%
    critical_threshold: -20%

# 进化触发阈值
evolution_trigger:
  minimum_degradation_days: 3      # 需要连续 N 天下降才触发
  minimum_impacted_sessions: 500    # 影响至少 N 次会话
  confidence_threshold: 0.80      # 模式识别置信度

# A/B 测试自动停止规则
ab_test_auto_stop:
  loser_significance: 0.98          # 变体失败置信度
  winner_significance: 0.95          # 变体胜出置信度
  max_test_duration_days: 30
  minimum_running_days: 7           # 最少运行 7 天
```

---

## 5. 与现有 Skills 的集成方案

### 5.1 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Evolution Engine                            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Metrics   │  │   Pattern   │  │  Strategy   │            │
│  │  Collector  │  │ Recognizer  │  │  Generator  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                              │                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   A/B Testing Framework                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
         ▲               ▲               ▲               ▲
         │               │               │               │
    ┌────┴────┐    ┌────┴────┐    ┌─────┴─────┐   ┌────┴────┐
    │ Observer│    │ Observer│    │ Observer  │   │ Observer│
    │ Hook   │    │ Hook    │    │ Hook      │   │ Hook    │
    └────┬────┘    └────┬────┘    └─────┬─────┘   └────┬────┘
         │               │               │               │
┌────────┴───────────────┴───────────────┴───────────────┴────────┐
│                      Skill Registry                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  seo-    │  geo-    │ seo-     │ content- │  other   │        │
│  content │  llmstxt │ technical│ writer   │  Skills  │        │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
```

### 5.2 角色定位

**Evolution Engine 作为 Skill 而非外部服务:**

```
Evolution Engine 的定位
├── 是 Skill 系统的"元层" (Meta-Layer)
├── 通过标准 Skill 接口与其他 Skills 通信
├── 使用 Skill Registry 发现和管理目标 Skills
└── 通过 MCP 协议调用外部数据源
```

**具体角色:**
1. **观察者 (Observer)**: 被动接收其他 Skills 的执行事件
2. **顾问 (Advisor)**: 向 Skills 提供优化建议，但不强制执行
3. **实验管理者 (Experiment Manager)**: 协调 A/B 测试的生命周期
4. **版本记录者 (Version Keeper)**: 维护 Skills 的版本演进历史

### 5.3 观察机制

```typescript
// Skill 执行事件标准格式
interface SkillExecutionEvent {
  eventId: string;
  timestamp: string;
  skillId: string;
  versionId: string;
  sessionId: string;

  // 执行上下文
  input: {
    parameters: Record<string, any>;
    userContext?: Record<string, any>;
  };

  output: {
    success: boolean;
    result?: any;
    error?: { code: string; message: string };
  };

  // 性能指标
  performance: {
    latencyMs: number;
    tokenUsage?: { input: number; output: number; total: number };
    cost?: number;
  };

  // 效果指标 (由 Skill 自行上报)
  effect?: {
    metricType: string;
    value: number;
    dimensions?: Record<string, string>;
  };
}

// Evolution Engine 观察者接口
interface EvolutionObserver {
  onSkillExecution(event: SkillExecutionEvent): void;
  onMetricThresholdBreached(alert: MetricAlert): void;
  onExternalDataUpdate(data: ExternalDataUpdate): void;
}
```

### 5.4 反馈机制

```typescript
// Evolution Engine 向 Skills 提供的反馈接口
interface SkillOptimizationFeedback {
  feedbackId: string;
  timestamp: string;
  targetSkillId: string;
  targetVersionId?: string;

  feedbackType: "optimization_suggestion" | "parameter_recommendation" | "prompt_hint";

  // 建议内容
  suggestions: {
    parameter?: string;
    currentValue?: any;
    recommendedValue?: any;
    rationale: string;
    expectedImpact: {
      metricType: string;
      expectedDelta: number;
      confidence: number;
    };
  }[];

  // 行动选项
  actions: {
    type: "apply_immediately" | "run_ab_test" | "review_and_apply";
    autoExecuteIfConfidenceAbove?: number;
  };

  // 关联数据
  supportingData: {
    patternType: string;
    confidence: number;
    sampleSize: number;
    historicalDataAvailable: boolean;
  };
}

// Skill 接受反馈的接口
interface SkillFeedbackReceiver {
  receiveOptimizationFeedback(feedback: SkillOptimizationFeedback): Promise<FeedbackResponse>;

  // 反馈处理结果
  // • accepted: 接受并应用到下一版本
  // • rejected: 拒绝，说明原因
  // • scheduled_for_test: 排入 A/B 测试
}

interface FeedbackResponse {
  feedbackId: string;
  status: "accepted" | "rejected" | "scheduled_for_test";
  nextAction?: {
    type: string;
    versionId?: string;
    scheduledTestId?: string;
  };
  rejectionReason?: string;
}
```

### 5.5 Skill 注册与发现

```typescript
// Skill Registry 条目
interface RegisteredSkill {
  skillId: string;
  skillName: string;
  category: "seo" | "geo" | "content" | "technical" | "other";

  // Evolution Engine 相关配置
  evolutionConfig: {
    enabled: boolean;
    autoApplySuggestions: boolean;     // 是否自动应用高置信度建议
    autoCreateABTest: boolean;          // 是否自动为新策略创建 A/B 测试
    minimumConfidenceThreshold: number; // 最小置信度阈值
  };

  // 版本历史
  versions: SkillVersion[];

  // 当前活跃版本
  activeVersionId: string;

  // 观察者列表
  observers: string[];  // Evolution Engine 的 observer IDs
}
```

---

## 6. 工作流时序图

### 6.1 日常监控流程

```
┌──────┐    ┌───────────────┐    ┌───────────────┐    ┌────────────────┐
│ Skill│    │  Evolution    │    │   Pattern     │    │   Strategy     │
│      │    │  Collector    │    │  Recognizer   │    │   Generator    │
└──┬───┘    └───────┬───────┘    └───────┬───────┘    └───────┬────────┘
   │                │                    │                     │
   │ Skill执行完成   │                    │                     │
   │───────────────▶│                    │                     │
   │                │                    │                     │
   │                │ 记录执行指标         │                     │
   │                │───────────────▶    │                     │
   │                │                    │                     │
   │                │                    │ 分析趋势             │
   │                │                    │───────────────▶     │
   │                │                    │                     │
   │                │                    │    检测到下降趋势     │
   │                │◀───────────────────│                     │
   │                │                    │                     │
   │                │ 触发进化评估         │                     │
   │                │───────────────────────────────────────────▶│
   │                │                    │                     │
   │                │                    │                     │ 生成候选策略
   │                │◀──────────────────────────────────────────│
   │                │                    │                     │
   │                │ 策略审查 (可选)      │                     │
   │                │───────────▶ [Human/Agent]                 │
   │                │                    │                     │
   │                │ 启动A/B测试         │                     │
   │                │───────────────────────────────────────────────────▶[A/B Framework]
   │                │                    │                     │                     │
   │                │◀──────────────────────────────────────────────────│
   │                │                    │                     │                     │
```

### 6.2 A/B 测试完整流程

```
┌────────────┐   ┌──────────────┐   ┌────────────┐   ┌───────────────┐   ┌────────────┐
│  Strategy  │   │    A/B       │   │  Variant A │   │   Variant B   │   │  Analytics │
│  Generator  │   │  Framework   │   │  (Control)  │   │  (Treatment)  │   │   Store    │
└─────┬──────┘   └──────┬───────┘   └─────┬──────┘   └──────┬───────┘   └─────┬──────┘
      │                 │                 │                 │                 │
      │ 创建测试         │                 │                 │                 │
      │────────────────▶│                 │                 │                 │
      │                 │                 │                 │                 │
      │                 │ 分配流量         │                 │                 │
      │                 │────────────────▶│                 │                 │
      │                 │                 │                 │                 │
      │                 │ 分配流量         │                 │                 │
      │                 │────────────────────────────────────────────────▶│
      │                 │                 │                 │                 │
      │                 │◀────────────────────────────────────────────────│
      │                 │                 │                 │                 │
      │                 │ 实时监控         │                 │                 │
      │                 │────────────────▶│                 │                 │
      │                 │                 │                 │                 │
      │                 │ 实时监控         │                 │                 │
      │                 │────────────────────────────────────────────────▶│
      │                 │                 │                 │                 │
      │                 │ 周期性检查       │                 │                 │
      │                 │ 统计显著性       │                 │                 │
      │                 │                 │                 │                 │
      │                 │ 达到显著性       │                 │                 │
      │                 │──────────┐      │                 │                 │
      │                 │          │      │                 │                 │
      │                 │◀─────────┘      │                 │                 │
      │                 │                 │                 │                 │
      │                 │ 推广胜出版本     │                 │                 │
      │                 │────────────────▶│                 │                 │
      │                 │                 │                 │                 │
      │                 │ 记录结果         │                 │                 │
      │                 │────────────────────────────────────────────────────────────────▶│
      │                 │                 │                 │                 │
      │                 │                 │                 │                 │
      ▼                 ▼                 ▼                 ▼                 ▼
   [完成]          [测试关闭]        [保留为基准]    [提升为Active]    [新版本记录]
```

---

## 7. 关键决策点及默认值

### 7.1 决策树

```
检测到指标下降
│
├── 是否连续下降?
│   ├── 否 (偶发性波动) → 记录, 继续监控
│   └── 是 (连续 N 天)
│       │
│       ├── 下降幅度是否超过阈值?
│       │   ├── 否 → 记录, 继续监控
│       │   └── 是 → 进入进化评估
│       │
│       └── 是否有足够的历史数据支持分析?
│           ├── 否 → 增加监控频率, 收集更多数据
│           └── 是
│               │
│               ├── 模式识别置信度 >= 80%?
│               │   ├── 否 → 增加观察期
│               │   └── 是
│               │       │
│               │       ├── 建议方案置信度 >= 85%?
│               │       │   ├── 否 → 创建 A/B 测试
│               │       │   └── 是
│               │       │       │
│               │       │       ├── autoApplySuggestions = true?
│               │       │       │   ├── 是 → 自动应用
│               │       │       │   └── 否 → 通知人工审批
│               │       │       │
│               │       └── 评估风险
│               │           │
│               │           ├── 高风险 → 强制 A/B 测试
│               │           └── 中低风险 → 按配置执行
```

### 7.2 默认配置值

```yaml
evolution_engine:
  # 数据收集配置
  metrics_collection:
    skill_execution_batch_size: 100
    flush_interval_seconds: 60
    external_data_fetch_timeout_ms: 30000
    retry_attempts: 3

  # Pattern Recognition 配置
  pattern_recognition:
    minimum_history_days: 7
    preferred_history_days: 30
    trend_significance_threshold: 0.7
    correlation_significance_threshold: 0.05
    outlier_detection_method: "iqr"  # or "zscore"

  # Strategy Generation 配置
  strategy_generation:
    max_candidates_per_round: 5
    minimum_expected_improvement: 0.05
    risk_tolerance: "medium"  # low, medium, high
    consider_token_cost: true
    consider_latency: true

  # A/B Testing 配置
  ab_testing:
    default_test_duration_days: 14
    minimum_sample_per_variant: 500
    significance_level: 0.95
    use_bayesian: false
    allow_early_stop: true
    traffic_allocation:
      control: 50
      variants: 50

  # 自动化级别
  automation:
    auto_create_tests: true
    auto_stop_losing_tests: true
    auto_promote_winners: false    # 默认需要人工确认
    auto_rollback_on_degradation: true
    rollback_threshold: -0.10

  # 通知配置
  notifications:
    enabled: true
    channels: ["log", "webhook"]
    alert_on_anomaly: true
    alert_on_test_complete: true
    alert_on_promotion: true
    alert_severity_threshold: "warning"
```

---

## 8. 数据存储架构

### 8.1 存储选型建议

| 数据类型 | 推荐存储 | 理由 |
|---------|---------|-----|
| 指标时序数据 | TimescaleDB / InfluxDB | 时序查询性能, 自动压缩 |
| 版本历史 | PostgreSQL | 关系型查询, 事务支持 |
| A/B 测试配置 | PostgreSQL | 结构化数据, 外键约束 |
| Skill 版本代码 | Git + 对象存储 | 版本控制, 差异对比 |
| 实时事件 | Redis / Kafka | 高吞吐, 实时处理 |
| 分析结果 | Elasticsearch | 全文搜索, 聚合分析 |

### 8.2 数据保留策略

```yaml
data_retention:
  raw_metrics:
    duration: 90 days
    aggregation_before_delete: true
    aggregated_metrics_retention: 2 years

  skill_versions:
    duration: forever
    archive_after_years: 1

  ab_test_results:
    duration: 1 year
    archive_after_years: 1

  pattern_analysis:
    duration: 2 years

  evolution_snapshots:
    duration: forever
    daily_snapshots_retention: 30 days
    weekly_snapshots_retention: 1 year
    monthly_snapshots_retention: forever
```

---

## 9. 安全性与权限

### 9.1 权限模型

```yaml
permissions:
  roles:
    - evolution_admin:
        - create_tests
        - approve_promotions
        - modify_thresholds
        - view_all_data

    - evolution_operator:
        - create_tests
        - view_reports
        - cannot_promote

    - skill_owner:
        - receive_feedback
        - apply_rejections
        - view_own_skill_metrics

    - readonly:
        - view_dashboards
        - view_reports
```

---

## 10. 扩展性设计

### 10.1 水平扩展

```
                    ┌─────────────────┐
                    │ Load Balancer   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐    ┌───────▼───────┐    ┌───────▼───────┐
│  Evolution    │    │  Evolution    │    │  Evolution    │
│  Engine #1    │    │  Engine #2    │    │  Engine #3    │
│               │    │               │    │               │
│ • Collector   │    │ • Collector   │    │ • Collector   │
│ • Recognizer  │    │ • Recognizer  │    │ • Recognizer  │
│ • Generator   │    │ • Generator   │    │ • Generator   │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared State    │
                    │ (Redis/Kafka)   │
                    └─────────────────┘
```

### 10.2 多租户支持

```typescript
interface TenantContext {
  tenantId: string;
  tenantName: string;
  quotas: {
    maxSkills: number;
    maxTestsPerMonth: number;
    maxDataRetentionDays: number;
  };
  features: {
    advancedAnalytics: boolean;
    customMetrics: boolean;
    whiteLabel: boolean;
  };
}
```

---

## 11. 监控与可观测性

### 11.1 关键指标

```yaml
observability:
  metrics:
    - name: skill_executions_total
      type: counter
      labels: [skill_id, version_id, status]

    - name: evolution_recommendations_total
      type: counter
      labels: [skill_id, recommendation_type]

    - name: ab_tests_active
      type: gauge
      labels: [skill_id]

    - name: ab_test_duration_hours
      type: histogram
      labels: [test_id, outcome]

    - name: feedback_accept_rate
      type: gauge
      labels: [skill_id]

    - name: metric_collection_latency_ms
      type: histogram
      labels: [data_source]

  alerts:
    - name: NoDataReceived
      condition: skill_executions_total == 0 for 1h
      severity: warning

    - name: HighTestFailureRate
      condition: ab_test_failure_rate > 0.1
      severity: critical

    - name: RecommendationStagnation
      condition: no_recommendations_generated for 7d
      severity: info
```

---

## 12. 实施建议

### 12.1 阶段一: 基础建设 (1-2 周)
1. 实现 Metrics Collector
2. 搭建基础数据存储
3. 集成 Google Search Console API
4. 创建 Skill Registry

### 12.2 阶段二: 核心逻辑 (2-3 周)
1. 实现 Pattern Recognizer
2. 实现 Strategy Generator
3. 开发 Dashboard
4. 告警系统

### 12.3 阶段三: A/B 测试 (2 周)
1. 实现 A/B Testing Framework
2. 流量分配算法
3. 统计分析模块
4. 自动停止规则

### 12.4 阶段四: 自动化 (1-2 周)
1. 实现完整触发链
2. 自动应用逻辑 (可选)
3. 回滚机制
4. 通知系统

### 12.5 阶段五: 优化 (持续)
1. 机器学习模型优化
2. 多数据源整合
3. 高级分析功能
4. 性能优化

---

## 13. 整合方案：clawd-code + geo-seo-openclaw-skills → 自进化 Skill 系统

### 13.1 三个来源的机制整合

| 来源 | 提供的机制 | 在进化系统中的角色 |
|------|-----------|-----------------|
| **clawd-code** | Prompt Routing (token匹配) | 意图识别路由层 |
| **clawd-code** | Reference Snapshots (JSON快照) | 版本化记录（每次执行的效果快照） |
| **clawd-code** | Parity Audit (覆盖率审计) | Skill 能力缺口发现 |
| **geo-seo-openclaw-skills** | SHEEP 框架 (S/H/E1/E2/P) | **效果指标体系**（Metrics Collector 的核心） |
| **geo-seo-openclaw-skills** | geo_optimizer.py (Python) | 可作为独立 Metrics 收集器 |
| **geo-seo-openclaw-skills** | platforms.json | 平台优化参数配置 |
| **Master Orchestrator** | Workflow A/B/C 执行框架 | 产生执行数据和 SHEEP 评分 |
| **Evolution Engine** | 4组件闭环 | 驱动版本演化和策略优化 |

### 13.2 自进化机制的核心逻辑

**"进化"的定义：基于 SHEEP 评分的闭环优化**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Master Orchestrator 执行工作流                     │
│                   (Workflow A: 全站 SEO+GEO 审计)                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   │  geo_optimizer.py     │
                   │  (SHEEP 评分引擎)      │
                   │                       │
                   │  S - 语义覆盖    (25%) │
                   │  H - 人类可信度  (25%) │
                   │  E1- 证据结构化  (20%) │
                   │  E2- 生态集成    (15%) │
                   │  P - 性能监测    (15%) │
                   │                       │
                   │  → 输出: GEM Score    │
                   └───────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │  写入: evolution-metrics/        │
              │  <execution_id>.json            │
              │  { gem_score, S, H, E1, E2, P } │
              └────────────────┬────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌─────────────┐      ┌─────────────────┐     ┌─────────────────┐
│Metrics      │      │Pattern          │     │Snapshot         │
│Collector    │ ───▶ │Recognizer       │     │Versioning       │
│(每次执行    │      │(SHEEP分数趋势)   │     │(clawd-code模式) │
│记录分数)    │      │                 │     │                 │
└──────┬──────┘      └────────┬────────┘     └────────┬────────┘
       │                      │                       │
       │              ┌───────▼────────┐             │
       │              │Strategy        │             │
       │              │Generator       │             │
       │              │(基于 SHEEP      │             │
       │              │ 维度弱点生成    │             │
       │              │ 优化策略)       │             │
       │              └───────┬────────┘             │
       │                      │                       │
       │              ┌───────▼────────┐             │
       │              │A/B Testing     │             │
       │              │Framework       │             │
       │              │(验证优化效果)   │             │
       │              └───────┬────────┘             │
       │                      │                       │
       │              ┌───────▼────────┐             │
       │              │Promote Winner │             │
       │              │→ 新版本固化   │◀────────────┘
       │              └───────────────┘
       │
       ▼
  (回到 Master Orchestrator，下一轮执行使用优化后的 Skill 版本)
```

### 13.3 SHEEP 框架与 Evolution Engine 的深度整合

#### Metrics Collection（效果收集）
```json
// evolution-metrics/<execution_id>.json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "workflow": "WORKFLOW_A",
  "inputs": { "url": "...", "keywords": [...] },
  "sheep_scores": {
    "S_semantic_coverage": { "raw": 75, "weight": 0.25, "weighted": 18.75 },
    "H_human_credibility": { "raw": 60, "weight": 0.25, "weighted": 15.0 },
    "E1_evidence_structuring": { "raw": 80, "weight": 0.20, "weighted": 16.0 },
    "E2_ecosystem_integration": { "raw": 55, "weight": 0.15, "weighted": 8.25 },
    "P_performance_monitoring": { "raw": 70, "weight": 0.15, "weighted": 10.5 }
  },
  "gem_score": 68.5,
  "gem_delta": -2.3,
  "gem_trend": "declining",
  "competitor_gem_avg": 72.1,
  "platform_scores": {
    "chatgpt": { "estimated_citation_probability": "+40%" },
    "perplexity": { "estimated_citation_rate": "3.2x" }
  },
  "skill_versions": {
    "seo-content": "v2.1.0",
    "geo-citability": "v1.3.0"
  }
}
```

#### Pattern Recognition（基于 SHEEP 维度的趋势分析）
```python
# SHEEP 维度趋势检测
TREND_RULES = {
    "S_declining": {
      "symptom": "gem_score.semantic_coverage < 70",
      "action": "建议增加内容深度和关键词覆盖",
      "platform": "ChatGPT, Perplexity"
    },
    "H_declining": {
      "symptom": "gem_score.human_credibility < 65",
      "action": "建议添加作者凭证和专业引用",
      "platform": "ChatGPT (+40% 引用)"
    },
    "E1_declining": {
      "symptom": "gem_score.evidence_structuring < 60",
      "action": "建议添加FAQ Schema和数据表格",
      "platform": "Google AI Overview (+13% 覆盖)"
    },
    "E2_declining": {
      "symptom": "gem_score.ecosystem_integration < 55",
      "action": "建议增加外链和社交信号",
      "platform": "Gemini"
    },
    "P_declining": {
      "symptom": "gem_score.performance_monitoring < 60",
      "action": "建议30天内更新内容",
      "platform": "Perplexity (3.2x 刷新效果)"
    }
}
```

#### Strategy Generation（基于 SHEEP 弱点的优化策略）
```python
# 策略生成：聚焦 SHEEP 中得分最低的维度
def generate_sheep_optimization_strategy(gem_scores, platforms):
    weakest_dim = min(gem_scores.items(), key=lambda x: x[1]['raw'])
    dim_name, dim_data = weakest_dim

    strategy = {
        "dimension": dim_name,
        "current_score": dim_data['raw'],
        "target_score": dim_data['raw'] + 15,
        "optimization_actions": SHEEP_OPTIMIZATION_TACTICS[dim_name],
        "expected_gem_boost": dim_data['weight'] * 15,
        "platform_priority": PLATFORM_WEIGHTS[dim_name]
    }
    return strategy

SHEEP_OPTIMIZATION_TACTICS = {
    "S_semantic_coverage": [
        "扩展内容至1500-2500词（ChatGPT最优长度）",
        "增加语义相关关键词覆盖",
        "添加相关长尾问题（H2-H3结构）"
    ],
    "H_human_credibility": [
        "添加作者简介和专业背景",
        "增加权威来源引用（PubMed, arXiv, Forbes）",
        "添加统计数据（+41% 引用效果）"
    ],
    "E1_evidence_structuring": [
        "添加FAQ Schema（JSON-LD）",
        "将数据表格化呈现",
        "增加HowTo结构化内容"
    ],
    "E2_ecosystem_integration": [
        "增加高质量外链（Wikipedia + 行业权威）",
        "社交媒体内容分发",
        "确保NAP一致性和品牌引用"
    ],
    "P_performance_monitoring": [
        "设置内容更新提醒（30天周期）",
        "添加最后更新日期标记",
        "建立内容刷新工作流"
    ]
}
```

### 13.4 Skill Snapshot 版本化（clawd-code 模式）

```json
// skills-snapshots/seo-content/v2.1.0.json
{
  "snapshot_id": "seo-content-v2.1.0-20260403",
  "skill_id": "seo-content",
  "version": "2.1.0",
  "created_at": "2026-04-03T00:00:00Z",
  "triggered_by": "gem_score_declining_H_dimension",
  "parameters": {
    "min_word_count": 1500,
    "max_word_count": 2500,
    "required_citations": 5,
    "citation_style": "apa",
    "eeat_weight": {
      "expertise": 0.30,
      "experience": 0.25,
      "authoritativeness": 0.25,
      "trustworthiness": 0.20
    }
  },
  "sheep_context": {
    "target_dimensions": ["H_human_credibility", "E1_evidence_structuring"],
    "target_platforms": ["chatgpt", "perplexity"],
    "expected_gem_boost": "+3.5"
  },
  "execution_stats": {
    "executions": 127,
    "avg_gem_score": 71.3,
    "avg_execution_time_ms": 8420
  }
}
```

### 13.5 Parity Audit - Skill 能力缺口发现

```python
# 缺口分析：当前 Skills vs 平台需求
PLATFORM_REQUIREMENTS = {
    "chatgpt": {
        "min_word_count": 1500,
        "required_elements": ["author_credentials", "primary_sources", "statistics"],
        "sheep_dimensions": ["S", "H"]
    },
    "perplexity": {
        "min_freshness_days": 30,
        "required_elements": ["inline_citations", "H2_H3_structure", "freshness_date"],
        "sheep_dimensions": ["S", "E1", "P"]
    },
    "google_ai_overview": {
        "required_elements": ["faq_schema", "direct_answer_first_150", "data_tables"],
        "sheep_dimensions": ["E1", "P"]
    }
}

def parity_audit(skill_versions, target_platform):
    """检查 Skill 能力是否满足平台需求"""
    required = PLATFORM_REQUIREMENTS[target_platform]
    gaps = []

    for skill_id, version in skill_versions.items():
        for element in required['required_elements']:
            if not skill_supports(skill_id, version, element):
                gaps.append({
                    "skill": skill_id,
                    "missing": element,
                    "platform": target_platform,
                    "sheep_dimension": required['sheep_dimensions']
                })

    return {
        "platform": target_platform,
        "coverage_score": 1 - (len(gaps) / len(required['required_elements'])),
        "gaps": gaps,
        "recommendation": f"优先补充 {gaps[0]['missing'] if gaps else '无'}"
    }
```

### 13.6 完整的自进化工作流

```
用户: /geo-site-audit https://example.com

Step 1: Master Orchestrator 执行 Workflow A
  └─▶ 并行调用 seo-technical, seo-content, geo-audit, etc.
  └─▶ 每个 Skill 产生自己的 findings

Step 2: geo_optimizer.py 计算 SHEEP 分数
  └─▶ 抓取网站内容 → 提取指标 → 计算 GEM Score
  └─▶ 输出: { S: 75, H: 58, E1: 80, E2: 62, P: 70 } → GEM: 68.5

Step 3: Metrics Collection (写入 Snapshot)
  └─▶ evolution-metrics/<execution_id>.json
  └─▶ skills-snapshots/seo-content/v2.1.0.json (更新)

Step 4: Pattern Recognizer (每日凌晨或手动)
  └─▶ 分析历史 GEM 趋势: { 68.5, 69.2, 67.8, 65.1 } → 下降中
  └─▶ 识别: H_dimension 持续下降（作者凭证缺失）
  └─▶ 识别: P_dimension 接近阈值（内容超过90天未更新）

Step 5: Strategy Generator
  └─▶ 聚焦 H 维度（权重25%，当前58分）
  └─▶ 生成策略: "添加作者简介 + 增加统计数据"
  └─▶ 预期 GEM 提升: +3.5

Step 6: A/B Testing (可选，默认自动应用)
  └─▶ 生成 Variant: seo-content-v2.2.0（增加作者凭证检查）
  └─▶ 50% 流量运行 v2.1.0, 50% 运行 v2.2.0
  └─▶ 监测 H_dimension 是否有提升

Step 7: Winner Promote
  └─▶ 如果 v2.2.0 在 H_dimension 提升 >10%，自动提升为 active
  └─▶ 更新 skills-snapshots/seo-content/v2.2.0.json
  └─▶ 下次执行使用 v2.2.0
```

### 13.7 整合后的完整 Skill 架构

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SEO/GEO Master Orchestrator                          │
│  Workflow A (全站审计) → Workflow B (关键词优化) → Workflow C (GEO)     │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  ┌─────────────┐       ┌─────────────┐        ┌─────────────┐
  │geo_optimizer│       │  Skills     │        │   Snapshots │
  │  (SHEEP)    │       │  Registry   │        │   Store     │
  │  Python     │       │  (clawd)    │        │  (clawd)    │
  └──────┬──────┘       └──────┬──────┘        └──────┬──────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │   Evolution Engine      │
                    │                         │
                    │  Metrics Collector      │◀── geo_optimizer.py 分数
                    │  Pattern Recognizer     │◀── 历史趋势分析
                    │  Strategy Generator     │◀── SHEEP 弱点策略
                    │  A/B Testing Framework  │◀── 流量分配验证
                    │  Snapshot Versioning    │◀── 版本化记录
                    │  Parity Audit           │◀── 能力缺口发现
                    └─────────────────────────┘
```

### 13.8 实施优先级

| 阶段 | 任务 | 产出 | 依赖 |
|------|------|------|------|
| **Phase 0** | 将 geo_optimizer.py 整合到 Master Orchestrator | SHEEP 评分成为工作流标准输出 | geo-seo-openclaw-skills |
| **Phase 1** | 实现 Metrics Collection + Snapshot Store | 每次执行自动记录 SHEEP 分数 | geo_optimizer.py |
| **Phase 2** | 实现 Pattern Recognizer | 检测 SHEEP 下降趋势，触发优化 | Phase 1 |
| **Phase 3** | 实现 Strategy Generator | 基于 SHEEP 弱点生成优化策略 | Phase 2 |
| **Phase 4** | 实现 A/B Testing Framework | 验证策略效果，胜出推广 | Phase 3 |
| **Phase 5** | 实现 Parity Audit | 发现 Skill vs 平台需求缺口 | All phases |

---

## 14. 整合方案：clawd-code + geo-seo-openclaw-skills → 自进化 Skill 系统

### 14.1 对两个项目的重新定位

经过对两个项目的深入分析，现对其在"自进化 Skill"架构中的角色重新定位：

| 项目 | 在自进化系统中的角色 | 提供的能力 |
|------|-------------------|----------|
| **clawd-code** | **基础设施层** | Prompt Routing、Snapshot 版本化、Parity Audit 框架 |
| **geo-seo-openclaw-skills** | **效果指标层** | SHEEP 评分体系、GEO 优化算法、平台特定策略 |

**关键洞察：** 这两个项目单独来看都不是完整的进化系统，但组合起来恰好互补。clawd-code 提供了进化的"骨架"（版本化、审计），geo-seo-openclaw-skills 提供了进化的"血液"（效果指标）。

### 14.2 问答四个核心问题

#### Q1: SHEEP 框架能否作为 Evolution Engine 的"效果指标体系"？

**答案：可以，但需要扩展。**

**SHEEP 的优势：**
- 5 维度设计成熟，覆盖 SEM、SEO、GEO 的核心评估维度
- GEM 综合评分提供单一可追踪指标
- 已有 `geo_optimizer.py` 实现，开箱即用

**与 Evolution Engine 数据模型的结合方式：**

```python
# Evolution Engine 的 EffectMetric 扩展 SHEEP 维度
EffectMetric = {
  "metricType": "sheep_gem_score",     # SHEEP 综合评分
  "dimensions": {
    "S_semantic_coverage": 75,         # 直接来自 geo_optimizer.py
    "H_human_credibility": 58,
    "E1_evidence_structuring": 80,
    "E2_ecosystem_integration": 62,
    "P_performance_monitoring": 70
  },
  "platformScores": {                   # 平台特定评分
    "chatgpt": 68,
    "perplexity": 72,
    "claude": 65,
    "gemini": 70,
    "google_ai_overview": 74
  }
}
```

**需要补充的能力：**
1. Skill 执行层面的指标（延迟、Token 消耗、错误率）→ 补充到 P (Performance Monitoring)
2. 业务层面的转化指标（用户的 SEO 排名变化、AI 引用率变化）→ 作为外部数据源拉取

#### Q2: clawd-code 的三个模式能否与 SHEEP 框架结合？

**答案：可以形成互补的闭环。**

| clawd-code 模式 | 与 SHEEP 的结合方式 |
|----------------|-------------------|
| **Prompt Routing** | 路由决策可以参考 SHEEP 分数：S/H 维度高的 Skill 优先路由 |
| **Reference Data Snapshots** | 每个 Snapshot 可以存储当时的 SHEEP 分数，实现"带评分的版本" |
| **Parity Audit** | Audit 可以发现 Skill 能力与 SHEEP 各维度要求之间的差距 |

**整合示意：**

```
SHEEP 评分系统 ──驱动──▶ Prompt Routing (优先路由高评分 Skill)
     │
     ▼
Snapshot 版本化 (每个版本记录当时的 SHEEP 分数)
     │
     ▼
Parity Audit (发现 Skill vs SHEEP 要求的差距)
     │
     ▼
Strategy Generator (生成弥补差距的策略)
```

#### Q3: "进化"这个词在 Boss 语境里的可能含义？

**传统理解：** 基于执行结果自动修改自身代码（自我编程）

**Boss 可能的替代理解：** 一个完整的**量化反馈闭环**

```
┌─────────────────────────────────────────────────────────────────┐
│  传统"进化" (self-modification)                                 │
│  Skill 自身代码 ──基于效果──▶ 修改自身代码                       │
│  ❌ 当前两个项目都不支持这个机制                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Boss 语境下的"进化" (量化反馈闭环)                              │
│                                                                  │
│  执行 Skill ──产生数据──▶ SHEEP 评分                            │
│       ▲                     │                                   │
│       │                     ▼                                   │
│       │              检测分数趋势                                 │
│       │                     │                                   │
│       │                     ▼                                   │
│       │              识别优化机会                                │
│       │                     │                                   │
│       │                     ▼                                   │
│       │              生成优化策略                                │
│       │                     │                                   │
│       │                     ▼                                   │
│       └────── 应用新版本 ◀───┘                                   │
│                                                                  │
│  ✅ 这正是 clawd-code + geo-seo-openclaw-skills 组合可以实现   │
└─────────────────────────────────────────────────────────────────┘
```

**关键区别：** 不是"修改 Skill 代码"，而是"通过版本迭代优化效果"。每次迭代都会产生新的 Snapshot 版本，记录新的 SHEEP 分数，形成可追溯的进化历史。

#### Q4: 整合方案的具体设计

**整体架构：**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         用户请求 (如 /geo audit)                            │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Master Orchestrator (clawd-code)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │ seo-        │  │ geo-        │  │ other-      │                        │
│  │ technical   │  │ ai-visibility│  │ skills      │                        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                        │
│         └─────────────────┼─────────────────┘                              │
│                           ▼                                                 │
│              ┌────────────────────────┐                                     │
│              │  geo_optimizer.py      │                                     │
│              │  (SHEEP 评分计算)      │                                     │
│              │  S/H/E1/E2/P → GEM    │                                     │
│              └───────────┬────────────┘                                     │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Evolution Engine (新增层)                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Metrics Collector                                                     │   │
│  │ • 接收 geo_optimizer.py 的 SHEEP 分数                                │   │
│  │ • 写入 Snapshot Store: evolution-metrics/<exec_id>.json              │   │
│  │ • 补充 Skill 执行指标: latency, tokens, error_rate                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern Recognizer                                                     │   │
│  │ • 分析 SHEEP 分数历史趋势: {68.5, 69.2, 67.8, 65.1} → 下降趋势     │   │
│  │ • 识别最弱维度: H (human_credibility) 持续走低                       │   │
│  │ • 检测异常波动: P (performance_monitoring) 突降                        │   │
│  │ • 关联外部事件: Google Core Update → E1/E2 维度影响                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Strategy Generator                                                     │   │
│  │ • 基于 SHEEP 弱点生成策略: "H 维度低 → 添加作者简介 + 增加引用"       │   │
│  │ • 计算预期提升: +3.5 GEM points                                       │   │
│  │ • 评估风险: low/medium/high                                          │   │
│  │ • 生成候选版本: v2.2.0 (H-focused optimization)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ A/B Testing Framework                                                │   │
│  │ • 流量分配: 50% v2.1.0 (control), 50% v2.2.0 (treatment)            │   │
│  │ • 统计检验: p < 0.05 显著性                                          │   │
│  │ • 提前停止: 胜出置信度 > 95% 时提前结束                               │   │
│  │ • 推广: winner 自动提升为 active                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌───────────────────────┐    ┌───────────────────────────────────────┐   │
│  │ Snapshot Store        │    │ Parity Audit                           │   │
│  │ (clawd-code)          │    │ (clawd-code)                           │   │
│  │                       │    │                                        │   │
│  │ skills-snapshots/     │    │ • Skill 能力 vs 平台需求差距            │   │
│  │  └─ seo-content/     │    │ • 发现缺失: Perplexity 需要新鲜度       │   │
│  │     ├─ v2.1.0.json  │    │   监测能力                              │   │
│  │     │  (GEM: 68.5)   │    │ • 发现缺失: Gemini 需要 Google         │   │
│  │     └─ v2.2.0.json  │    │   生态集成                               │   │
│  │        (GEM: 72.1)   │    │                                        │   │
│  └───────────────────────┘    └───────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**整合后的数据流：**

```python
# 整合后的 Skill 执行流程
class EvolutionAwareSkill:
    def execute(self, input_data):
        # 1. 执行 Skill 逻辑
        result = self.original_execute(input_data)

        # 2. 调用 geo_optimizer.py 计算 SHEEP 分数
        sheep_scores = run_geo_optimizer(result['content'])

        # 3. 写入 Snapshot (clawd-code 模式)
        write_snapshot(
            skill_id=self.skill_id,
            version=self.version,
            content=result['content'],
            sheep_scores=sheep_scores,  # 新增：带评分的版本
            execution_metrics={
                'latency_ms': result['latency'],
                'tokens': result['token_count'],
                'error_rate': result['errors'] / result['total']
            }
        )

        # 4. 触发 Pattern Recognizer (如果有新数据)
        if should_analyze():
            analyze_sheep_trends(self.skill_id)

        return result

    def should_analyze() -> bool:
        """判断是否触发分析"""
        return (
            has_new_snapshot() and
            (snapshot_count() >= MIN_SAMPLES_FOR_TREND) and
            time_since_last_analysis() > ANALYSIS_INTERVAL
        )
```

### 14.3 整合方案的关键决策

#### 决策 1: "进化"粒度

| 粒度 | 描述 | 优势 | 劣势 |
|------|------|------|------|
| **Skill 版本级别** | 每个 Skill 的 v1, v2, v3... | 清晰、可追溯 | 迭代周期长 |
| **参数级别** | Skill 内部的参数配置迭代 | 快速反馈 | 复杂度高 |
| **两者结合** | Skill 版本记录大变化，参数记录微调 | 平衡灵活性和可追溯性 | 需要两层追踪 |

**推荐：Skill 版本级别** — 与 clawd-code 的 Snapshot 机制天然对齐

#### 决策 2: Snapshot 存储结构扩展

```json
{
  "version": "v2.1.0",
  "skill_id": "seo-content",
  "created_at": "2026-04-03T10:30:00Z",
  "sheep_scores": {
    "semantic_coverage": 75,
    "human_credibility": 58,
    "evidence_structuring": 80,
    "ecosystem_integration": 62,
    "performance_monitoring": 70,
    "gem_score": 68.5
  },
  "platform_scores": {
    "chatgpt": 68,
    "perplexity": 72,
    "claude": 65,
    "gemini": 70,
    "google_ai_overview": 74
  },
  "execution_metrics": {
    "avg_latency_ms": 1200,
    "token_cost_per_exec": 3500,
    "error_rate": 0.02
  },
  "change_summary": "添加了作者凭证检查和内容深度分析",
  "parent_version": "v2.0.0"
}
```

#### 决策 3: 触发自动化的阈值

```yaml
automation_thresholds:
  # Pattern Recognizer 触发
  trend_detection:
    minimum_samples: 5           # 至少 5 个数据点
    significance_threshold: 0.7   # 趋势置信度 > 70%
    minimum_delta: 3.0           # 分数变化 > 3 分

  # Strategy Generator 触发
  strategy_generation:
    minimum_gem_gap: 5.0        # GEM 分数与目标差距 > 5
    weakest_dimension_weight: 0.25  # 最弱维度权重 > 25%

  # A/B Test 自动停止
  ab_test_early_stop:
    winner_significance: 0.95     # 胜出置信度 > 95%
    loser_significance: 0.90     # 失败置信度 > 90%
    minimum_duration_hours: 24   # 最少运行 24 小时
```

### 14.4 与原始 Evolution Engine 设计的对应关系

| 原始 Evolution Engine 组件 | 整合后的实现 | 数据来源 |
|--------------------------|------------|---------|
| **Metrics Collector** | SHEEP 评分收集器 | `geo_optimizer.py` + Skill 执行日志 |
| **Pattern Recognizer** | 分数趋势分析器 | Snapshot Store 时间序列 |
| **Strategy Generator** | 优化策略生成器 | SHEEP 弱点 + 平台要求 |
| **A/B Testing Framework** | 版本对比器 | Snapshot Store + 流量分配 |
| **Snapshot Versioning** | clawd-code Snapshot Store | `skills-snapshots/` 目录 |
| **Parity Audit** | 能力差距发现器 | 平台要求 vs Skill 能力 |

### 14.5 实施路线图

```
Phase 0: 整合 geo_optimizer.py (1 周)
├── 将 geo_optimizer.py 作为 SHEEP 评分引擎集成到 Master Orchestrator
├── 定义 Snapshot 数据模型扩展 (包含 sheep_scores)
└── 产出: 每次 Skill 执行自动输出 SHEEP 分数

Phase 1: 实现 Snapshot Versioning (1 周)
├── 扩展 clawd-code Snapshot Store 支持 SHEEP 分数
├── 实现版本历史存储和查询
└── 产出: skills-snapshots/<skill>/<version>.json (带评分)

Phase 2: 实现 Metrics Collection + Pattern Recognizer (2 周)
├── 从 Snapshot Store 提取时间序列数据
├── 实现趋势检测算法 (移动平均 + 异常检测)
├── 设置告警阈值
└── 产出: 分数下降时自动告警

Phase 3: 实现 Strategy Generator (1-2 周)
├── 基于 SHEEP 弱点维度生成优化策略
├── 调用 LLM 生成具体修改建议
└── 产出: 优化建议报告

Phase 4: 实现 A/B Testing Framework (2 周)
├── 扩展 Snapshot Store 支持多版本并行
├── 实现流量分配算法
├── 实现统计显著性检验
└── 产出: 自动版本对比和胜出推广

Phase 5: 实现 Parity Audit (1 周)
├── 定义平台能力要求矩阵
├── 实现 Skill 能力自动评估
└── 产出: 能力差距报告
```

### 14.6 结论

**整合后的"自进化 Skill 系统"定义：**

> 通过 SHEEP 量化指标追踪 Skill 效果波动，通过 clawd-code Snapshot 版本化记录每个版本的效果，通过 Parity Audit 发现能力差距，通过 Strategy Generator 生成优化建议，通过 A/B Testing 验证策略有效性——这一整个**量化反馈闭环**，构成 Skill 的"进化"机制。

**关键特点：**
- 不是"修改 Skill 代码"而是"通过版本迭代优化效果"
- 进化粒度是 Skill 版本，不是代码自我修改
- 每次迭代都有量化指标（SHEEP）支撑决策
- 进化历史完整可追溯（Snapshot Store）

这个整合方案既利用了 clawd-code 的基础设施（Snapshot、Parity Audit、Prompt Routing），又利用了 geo-seo-openclaw-skills 的效果指标体系（SHEEP），形成了一个完整的自进化 Skill 系统。
