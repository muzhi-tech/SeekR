# SeekR Evolution — Architecture Plan v1.0

**Date:** 2026-04-03
**Status:** Baseline v1.0 — Implementation Planned
**Based on:** CLAWD-CODE architecture analysis + GEO/SEO domain expertise

---

## 1. Project Overview

**SeekR** is an autonomous SEO + GEO agent for English independent sites, with a self-evolution engine that continuously improves based on execution metrics.

- **Core Skills:** `seekr` (orchestrator), `seekr-evolve` (evolution engine)
- **Target:** English independent sites (ChatGPT, Perplexity, Claude, Gemini visibility)
- **Scoring:** SHEEP/GEM framework (S/H/E1/E2/P dimensions)
- **Evolution Goal:** Closed-loop self-improvement based on quantified metrics

---

## 2. CLAWD-CODE Reference Architecture

**Source:** https://github.com/godfalcon/clawd-code/tree/main/src
**Analysis:** `CLAWD-CODE-DEEP-ANALYSIS.md`

### 2.1 Seven Architecture Patterns Found

| # | Pattern | File | Description |
|---|---|---|---|
| 1 | **Snapshot + LRU Cache** | `tools.py`, `commands.py` | JSON snapshots loaded as immutable tuples via `@lru_cache` |
| 2 | **Parity Audit (5-dim)** | `parity_audit.py` | Coverage metrics: root files, directories, total files, commands, tools |
| 3 | **Token Scoring Route** | `runtime.py` | Prompt tokenized → matched against name/hint/responsibility → scored |
| 4 | **History Event Log** | `history.py` | Immutable `HistoryEvent` list, append-only |
| 5 | **Cost Tracker** | `cost_tracker.py` | Accumulator pattern: `record(label, units)` |
| 6 | **Porting Backlog** | `models.py` | Task registry with status tracking |
| 7 | **Tool Definition Registry** | `Tool.py` | Frozen dataclass tuples as global registries |

### 2.2 CLAWD-CODE Core Limitation

> **CLAWD-CODE is a STATIC MIRRORING system. There is NO feedback loop.**

```
route_prompt() → selects route → NO tracking of success/failure → NO score adjustment
run_parity_audit() → reports gaps → NO automatic remediation
```

**This is the exact gap SeekR must fill.**

---

## 3. SeekR Architecture v1.0

### 3.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Request                                  │
│                 (audit / evolve / article / optimize)                  │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        seekr (Orchestrator)                          │
│                                                                      │
│   Workflow A — Full SEO+GEO Audit                                   │
│   Workflow B — Keyword-Driven Optimization                            │
│   Workflow C — GEO AI Visibility Enhancement                          │
│   Workflow D — GEO Article Auto-Generation                            │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌────────────┐ ┌────────────┐ ┌────────────────┐
        │geo_optimizer│ │  Skills    │ │   Snapshots    │
        │ (SHEEP)    │ │  Registry  │ │   Store        │
        └─────┬──────┘ └─────┬──────┘ └───────┬────────┘
                │              │                │
                ▼              ▼                ▼
        ┌─────────────────────────────────────────────┐
        │           seekr-evolve (Evolution Engine)     │
        │                                              │
        │  ┌──────────────┐  ┌───────────────────┐   │
        │  │   Effect     │  │     Pattern       │   │
        │  │  Collector   │──│   Recognizer      │   │
        │  └──────────────┘  └─────────┬─────────┘   │
        │                                 │             │
        │  ┌──────────────┐  ┌─────────▼──────────┐  │
        │  │   A/B Test   │◀─│   Strategy         │  │
        │  │  Controller  │  │   Generator        │  │
        │  └──────┬──────┘  └─────────┬──────────┘  │
        │         │                     │              │
        │  ┌──────▼────────────────────▼──────────┐   │
        │  │     Snapshot + Parity Audit           │   │
        │  │     (CLAWD-CODE Pattern 1+2+6)        │   │
        │  └───────────────────────────────────────┘   │
        └─────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
seekr execution
    │
    ▼
evolution-metrics/<execution_id>.json
    │ (SHEEP scores, execution time, skills invoked, errors)
    │
    ▼
seekr-evolve / Effect Collector
    │
    ▼
Pattern Recognizer (trend detection, z-score, SHEEP dimension analysis)
    │
    ▼
Strategy Generator (threshold adjustment, trigger refinement, weight reallocation)
    │
    ▼
A/B Test Controller (10% traffic, p<0.05 significance, early stop)
    │
    ▼
Snapshot Versioning (draft → candidate → stable → archived)
    │
    ▼
Parity Audit (5-dim coverage check — gate for promotion)
```

---

## 4. CLAWD-CODE Patterns → SeekR Implementation

### 4.1 Pattern 1: Snapshot + LRU Cache

**CLAWD-CODE:**
```python
@lru_cache(maxsize=1)
def load_tool_snapshot() -> tuple[PortingModule, ...]:
    raw_entries = json.loads(SNAPSHOT_PATH.read_text())
    return tuple(PortingModule(...) for entry in raw_entries)
```

**SeekR Implementation:**
```
seekr/evolution-patterns/
├── evolution-snapshot.json    # Current evolution pattern registry
├── skill-registry.json        # All integrated skills metadata
├── sheep-baseline.json        # SHEEP score baselines
└── platform-config.json       # Platform-specific parameters
```

**Purpose:** Versioned snapshots of evolution patterns, baselines, and configurations.

### 4.2 Pattern 2: Parity Audit (5 Dimensions)

**CLAWD-CODE:**
```python
@dataclass(frozen=True)
class ParityAuditResult:
    root_file_coverage: tuple[int, int]      # (matched, total)
    directory_coverage: tuple[int, int]     # (matched, total)
    total_file_ratio: tuple[int, int]       # Python vs TS
    command_entry_ratio: tuple[int, int]    # command entries
    tool_entry_ratio: tuple[int, int]        # tool entries
```

**SeekR Parity Audit (5 Dimensions):**

```python
@dataclass(frozen=True)
class EvolutionParityResult:
    trigger_coverage: tuple[int, int]       # (covered, total trigger phrases)
    sheep_dimension_coverage: tuple[int, int] # (S/H/E1/E2/P all scored)
    workflow_coverage: tuple[int, int]       # (A/B/C/D workflows functional)
    skill_coverage: tuple[int, int]          # (integrated, total available)
    evolution_action_coverage: tuple[int, int] # (actions tested, total patterns)
```

**Purpose:** Audit that evolution changes don't break existing capabilities.

### 4.3 Pattern 3: Token Scoring Route

**CLAWD-CODE:**
```python
def route_prompt(prompt: str, limit=5):
    tokens = {token.lower() for token in prompt.replace('/', ' ').replace('-', ' ').split()}
    by_kind = {
        'command': _collect_matches(tokens, PORTED_COMMANDS, 'command'),
        'tool': _collect_matches(tokens, PORTED_TOOLS, 'tool'),
    }
    selected = []
    for kind in ('command', 'tool'):
        if by_kind[kind]:
            selected.append(by_kind[kind].pop(0))
    return selected
```

**SeekR Evolution Intent Detection:**

```python
def route_evolution_intent(prompt: str, limit=5):
    tokens = tokenize(prompt.lower())
    by_type = {
        'audit': find_audit_matches(tokens),      # "check", "audit", "status"
        'evolve': find_evolve_matches(tokens),   # "evolve", "improve", "optimize"
        'test': find_test_matches(tokens),        # "test", "ab", "experiment"
        'rollback': find_rollback_matches(tokens), # "rollback", "revert"
    }
    selected = []
    for kind in ('audit', 'evolve', 'test', 'rollback'):
        if by_type[kind]:
            selected.append(by_type[kind].pop(0))
    return selected
```

### 4.4 Pattern 4: History Event Log

**CLAWD-CODE:**
```python
@dataclass(frozen=True)
class HistoryEvent:
    title: str
    detail: str

@dataclass
class HistoryLog:
    events: list[HistoryEvent] = field(default_factory=list)
    def add(self, title: str, detail: str):
        self.events.append(HistoryEvent(title=title, detail=detail))
```

**SeekR Evolution Event Log:**

```python
@dataclass(frozen=True)
class EvolutionEvent:
    timestamp: str            # ISO8601
    event_type: str           # 'pattern_applied' | 'test_started' | 'version_promoted' | 'rollback_triggered'
    pattern_id: str            # Which evolution pattern was used
    target_skill: str          # Which skill was evolved
    outcome: str               # 'success' | 'degradation' | 'inconclusive'
    gem_score_delta: float     # Change in GEM score
    sheep_dimension_delta: dict # { 'S': +2.1, 'H': -1.3, ... }

@dataclass
class EvolutionHistory:
    events: list[EvolutionEvent] = field(default_factory=list)
    def add(self, event: EvolutionEvent):
        self.events.append(event)
    def get_success_rate(self, pattern_id: str) -> float:
        # pattern_id 被使用后成功的比率 → 调整 pattern 的 base_score
```

**This IS the feedback loop that CLAWD-CODE lacks.**

### 4.5 Pattern 5: Cost Tracker

**CLAWD-CODE:**
```python
@dataclass
class CostTracker:
    total_units: int = 0
    events: list[str] = field(default_factory=list)
    def record(self, label: str, units: int):
        self.total_units += units
        self.events.append(f'{label}:{units}')
```

**SeekR Evolution Cost Model:**

```python
@dataclass
class EvolutionCostTracker:
    total_cost: float = 0.0
    per_pattern_cost: dict[str, float] = field(default_factory=dict)
    per_skill_cost: dict[str, float] = field(default_factory=dict)
    per_test_cost: dict[str, float] = field(default_factory=dict)
    tokens_spent: int = 0

    def record(self, pattern_id: str, skill: str, cost: float, tokens: int):
        self.total_cost += cost
        self.per_pattern_cost[pattern_id] = self.per_pattern_cost.get(pattern_id, 0) + cost
        self.per_skill_cost[skill] = self.per_skill_cost.get(skill, 0) + cost
        self.tokens_spent += tokens

    def get_roi(self, pattern_id: str) -> float:
        # pattern 的 cost vs 它带来的 GEM 提升
```

### 4.6 Pattern 6: Porting Backlog

**CLAWD-CODE:**
```python
@dataclass
class PortingBacklog:
    title: str
    modules: list[PortingModule] = field(default_factory=list)

    def summary_lines(self):
        return [
            f'- {module.name} [{module.status}] — {module.responsibility}'
            for module in self.modules
        ]
```

**SeekR Evolution Backlog:**

```python
@dataclass
class EvolutionBacklog:
    title: str
    candidates: list[EvolutionCandidate] = field(default_factory=list)
    # candidates sorted by: expected_gem_boost / risk_score

@dataclass
class EvolutionCandidate:
    pattern_id: str
    target_skill: str
    expected_gem_boost: float
    risk_score: float  # 1.0 (low risk) to 3.0 (high risk)
    status: str         # 'proposed' | 'testing' | 'promoted' | 'rejected'
    sheep_dimension: str # Which SHEEP dim this targets

    def priority_score(self) -> float:
        return self.expected_gem_boost / self.risk_score
```

### 4.7 Pattern 7: Tool Definition Registry

**CLAWD-CODE:**
```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str

DEFAULT_TOOLS = (
    ToolDefinition('port_manifest', 'Summarize the active Python workspace'),
    ToolDefinition('query_engine', 'Render a Python-first porting summary'),
)
```

**SeekR Evolution Tool Registry:**

```python
@dataclass(frozen=True)
class EvolutionToolDefinition:
    name: str
    description: str
    category: str          # 'audit' | 'strategy' | 'test' | 'snapshot'
    pattern_count: int      # How many patterns this tool can apply

DEFAULT_EVOLUTION_TOOLS = (
    EvolutionToolDefinition('effect_collector', 'Collect execution metrics', 'audit', 0),
    EvolutionToolDefinition('pattern_recognizer', 'Detect score trends and degradation', 'audit', 0),
    EvolutionToolDefinition('strategy_generator', 'Generate evolution candidates', 'strategy', 7),
    EvolutionToolDefinition('ab_controller', 'Run A/B tests for candidates', 'test', 0),
    EvolutionToolDefinition('snapshot_manager', 'Version skill snapshots', 'snapshot', 0),
    EvolutionToolDefinition('parity_auditor', 'Audit evolution changes for regressions', 'audit', 5),
)
```

---

## 5. Feedback Loop (The Missing Piece)

This is the core innovation SeekR adds over CLAWD-CODE.

### 5.1 Feedback Loop Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP                             │
│                                                              │
│  Pattern Applied ──▶ Outcome Measured ──▶ Score Adjusted   │
│                                                              │
│  1. EvolutionEvent recorded (success/failure)                │
│  2. Success rate per pattern_id calculated                  │
│  3. Pattern base_score adjusted:                              │
│     new_score = base_score * (1 + success_rate_delta)      │
│  4. High-performing patterns get promoted more quickly        │
│  5. Low-performing patterns get deprioritized                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Feedback Score Adjustment

```python
@dataclass
class EvolutionPattern:
    pattern_id: str
    name: str
    base_score: float       # Initial score (1.0)
    success_count: int = 0
    failure_count: int = 0

    def adjusted_score(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return self.base_score
        success_rate = self.success_count / total
        # Boost if >60% success, penalize if <40%
        if success_rate > 0.6:
            return self.base_score * (1 + (success_rate - 0.6))
        elif success_rate < 0.4:
            return self.base_score * (0.5 + success_rate)
        return self.base_score
```

### 5.3 Auto-Rollback Trigger

```python
def should_auto_rollback(gem_delta: float, z_score: float) -> bool:
    # Trigger rollback if:
    # 1. GEM score dropped > 10 points
    # 2. z-score < -3.0 (99.7% confidence of degradation)
    return gem_delta < -10.0 or z_score < -3.0
```

---

## 6. Implementation Phases

### Phase 1: Core Integration (v1.0)
- [x] `seekr` skill: 4 workflows (A/B/C/D) with SHEEP scoring
- [x] `seekr-evolve` skill: Effect Collector + Pattern Recognizer
- [x] `SKILLS-REGISTRY.json`: All integrated skills
- [x] `geo_optimizer.py`: SHEEP scoring engine
- [ ] **NEW**: `evolution-patterns/` JSON snapshots
- [ ] **NEW**: Evolution Feedback Loop (history → score adjustment)
- [ ] **NEW**: Parity Audit (5-dim coverage check)

### Phase 2: Advanced Evolution (v1.1)
- [ ] Strategy Generator (7 pattern types)
- [ ] A/B Test Controller (10% traffic, p<0.05)
- [ ] Snapshot Versioning (draft → candidate → stable)
- [ ] Token-based Evolution Intent Detection

### Phase 3: Full Autonomy (v1.2)
- [ ] Auto-rollback on z-score < -3.0
- [ ] Scheduled evolution (daily at 03:00 UTC)
- [ ] Pattern ROI tracking
- [ ] Evolution Cost Model

---

## 7. File Structure (v1.0 Target)

```
seekr/
├── README.md
├── CLAWD-CODE-DEEP-ANALYSIS.md      ← Reference analysis
├── SEEKR-EVOLUTION-PLAN-v1.md      ← This file
├── SKILLS-REGISTRY.json
├── seekr-SKILL.md                   ← /seekr
├── seekr-evolve-SKILL.md            ← /seekr-evolve
│
└── evolution/
    ├── __init__.py
    ├── evolution-patterns/           ← Snapshot store (Pattern 1)
    │   ├── evolution-snapshot.json
    │   ├── skill-registry.json
    │   └── sheep-baseline.json
    ├── parity_audit.py               ← 5-dim parity (Pattern 2)
    ├── evolution_intent.py           ← Token routing (Pattern 3)
    ├── evolution_history.py          ← Event log (Pattern 4)
    ├── evolution_cost.py             ← Cost tracker (Pattern 5)
    ├── evolution_backlog.py          ← Candidate queue (Pattern 6)
    ├── evolution_tools.py            ← Tool registry (Pattern 7)
    └── feedback_loop.py             ← NEW: core innovation
```

---

## 8. Key Differences from CLAWD-CODE

| Dimension | CLAWD-CODE | SeekR |
|---|---|---|
| **Purpose** | Static TypeScript→Python mirroring | Dynamic self-evolving agent |
| **Feedback Loop** | None | Full: event → score → adjustment |
| **Snapshot Data** | Static reference only | Dynamic with version history |
| **Parity Audit** | File presence only | Capability coverage |
| **Routing** | Static token scoring | Dynamic with feedback adjustment |
| **Error Recovery** | None | Auto-rollback via z-score |
| **Cost Model** | Simple accumulator | ROI-based |

---

## 9. References

- **CLAWD-CODE:** https://github.com/godfalcon/clawd-code
- **SheepGeo SHEEP Framework:** https://github.com/CN-Sheep/SheepGeo
- **SeekR GitHub:** https://github.com/muzhi-tech/SeekR

---

**Version: 1.0.0 — Baseline for SeekR Evolution Architecture**
