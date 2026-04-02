# CLAWD-CODE Deep Analysis

Source: https://github.com/godfalcon/clawd-code/tree/main/src

## Repository Overview

CLAWD-CODE is a Python porting workspace for a Claude Code TypeScript-to-Python rewrite effort. It implements a **snapshot-based mirroring architecture** where TypeScript source is analyzed and mirrored as Python with parity auditing.

---

## File-by-File Analysis

---

### 1. `runtime.py`

**行数**: 72

**核心类/函数**:
- `PortRuntime` (line 11) — Prompt routing engine for matching user prompts to mirrored commands/tools
- `route_prompt(prompt, limit=5)` (line 13) — Tokenizes prompt, collects matches by kind, returns ranked results
- `_collect_matches(tokens, modules, kind)` (line 37) — Helper to score and filter matches
- `_score(tokens, module)` (line 47) — Static scoring method using keyword overlap

**关键实现模式**:

```python
# Token-based prompt parsing (line 14)
tokens = {token.lower() for token in prompt.replace('/', ' ').replace('-', ' ').split() if token}

# Dual-kind routing (lines 16-22)
by_kind = {
    'command': self._collect_matches(tokens, PORTED_COMMANDS, 'command'),
    'tool': self._collect_matches(tokens, PORTED_TOOLS, 'tool'),
}

# Ensure at least one representative from each kind (lines 24-27)
for kind in ('command', 'tool'):
    if by_kind[kind]:
        selected.append(by_kind[kind].pop(0))

# Scoring: token appears in name OR source_hint OR responsibility (lines 51-56)
haystacks = [module.name.lower(), module.source_hint.lower(), module.responsibility.lower()]
score = sum(1 for token in tokens if any(token in h for h in haystacks))
```

**数据传输格式**:
```python
@dataclass(frozen=True)
class RoutedMatch:
    kind: str       # 'command' or 'tool'
    name: str       # module name
    source_hint: str
    score: int      # token overlap count
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Token-based prompt routing** — Could be used for SeekR to route evolution suggestions to specific subsystems
2. **Dual-kind classification** — The pattern of routing to "command" vs "tool" mirrors how SeekR could route "improvement" vs "audit" tasks
3. **Score-based ranking** — The multi-factor sort key `(-item.score, item.kind, item.name)` shows priority weighting

**缺陷/限制**:
1. No learning/adaptation — scores are static, not updated based on usage patterns
2. No feedback loop — doesn't track which routes were selected and whether they were successful

---

### 2. `parity_audit.py`

**行数**: 120

**核心类/函数**:
- `ParityAuditResult` (line 31) — Frozen dataclass holding audit results
- `to_markdown()` (line 45) — Formats audit results as Markdown report
- `run_parity_audit()` (line 79) — Main audit function comparing Python workspace against TypeScript archive

**关键实现模式**:

```python
# Multiple coverage metrics tracked (lines 82-88)
root_file_coverage: tuple[int, int]    # matched root files / total targets
directory_coverage: tuple[int, int]    # matched directories / total targets
total_file_ratio: tuple[int, int]      # Python files / archived TS files
command_entry_ratio: tuple[int, int]  # command entries / expected
tool_entry_ratio: tuple[int, int]     # tool entries / expected

# Missing target tracking (lines 89-90)
missing_root_targets: tuple[str, ...]
missing_directory_targets: tuple[str, ...]

# Archive root detection (line 14)
ARCHIVE_ROOT = Path(__file__).resolve().parent.parent / 'archive' / 'claude_code_ts_snapshot' / 'src'

# File existence check via set membership (line 82)
current_entries = {path.name for path in CURRENT_ROOT.iterdir()}
root_hits = [target for target in ARCHIVE_ROOT_FILES.values() if target in current_entries]
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Parity audit pattern** — SeekR could audit itself: current capability vs desired capability
2. **Coverage metrics as tuple** — `(actual, expected)` format is clean and informative
3. **Missing target tracking** — Identify gaps in implementation
4. **Archive-based comparison** — The concept of comparing against a "golden source" snapshot

**缺陷/限制**:
1. Only checks file presence, not content correctness
2. No automatic remediation — only reports gaps
3. Hardcoded archive path — not configurable

---

### 3. `cost_tracker.py`

**行数**: 14

**核心类/函数**:
- `CostTracker` (line 6) — Simple cost tracking dataclass
- `record(label, units)` (line 10) — Records a cost event

**关键实现模式**:
```python
@dataclass
class CostTracker:
    total_units: int = 0
    events: list[str] = field(default_factory=list)

    def record(self, label: str, units: int) -> None:
        self.total_units += units
        self.events.append(f'{label}:{units}')  # Simple string formatting
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Event logging with labels** — SeekR could track "evolution cost" per subsystem
2. **Accumulator pattern** — Simple but effective for tracking usage

**缺陷/限制**:
1. No time-series tracking (when did costs occur)
2. No per-subsystem breakdown
3. Events are strings, not structured data

---

### 4. `history.py`

**行数**: 17

**核心类/函数**:
- `HistoryEvent` (line 8) — Frozen dataclass for single event
- `HistoryLog` (line 12) — Event container with `add()` method

**关键实现模式**:
```python
@dataclass(frozen=True)
class HistoryEvent:
    title: str
    detail: str

@dataclass
class HistoryLog:
    events: list[HistoryEvent] = field(default_factory=list)

    def add(self, title: str, detail: str) -> None:
        self.events.append(HistoryEvent(title=title, detail=detail))
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **History event sourcing** — SeekR could maintain a history of evolution decisions and outcomes
2. **Frozen events** — Immutable history records prevent tampering

**缺陷/限制**:
1. No persistence (in-memory only)
2. No query/filter capabilities
3. No timestamps

---

### 5. `models.py`

**行数**: 35

**核心类/函数**:
- `Subsystem` (line 8) — Represents a code subsystem with metadata
- `PortingModule` (line 13) — Represents a ported module with responsibility description
- `PortingBacklog` (line 18) — Container for tracking porting progress

**关键实现模式**:
```python
@dataclass(frozen=True)
class Subsystem:
    name: str
    path: str
    file_count: int
    notes: str

@dataclass(frozen=True)
class PortingModule:
    name: str
    responsibility: str
    source_hint: str
    status: str = 'planned'  # Default status

@dataclass
class PortingBacklog:
    title: str
    modules: list[PortingModule] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        return [
            f'- {module.name} [{module.status}] — {module.responsibility} (from {module.source_hint})'
            for module in self.modules
        ]
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Responsibility field** — Each evolution target should have a clear responsibility description
2. **Status tracking** — "planned", "in_progress", "completed" states
3. **Source hint** — Track where the pattern/implementation came from

**缺陷/限制**:
1. No state machine for status transitions
2. No validation that status changes are legal

---

### 6. `tools.py`

**行数**: 62

**核心类/函数**:
- `load_tool_snapshot()` (line 14) — Loads JSON snapshot with LRU cache
- `PORTED_TOOLS` (line 27) — Global tuple of mirrored tools
- `find_tools(query, limit)` (line 46) — Search by name or source_hint
- `tool_names()` (line 42) — List all tool names
- `get_tool(name)` (line 36) — Exact lookup
- `render_tool_index(limit, query)` (line 52) — Formatted output

**关键实现模式**:
```python
# LRU-cached snapshot loading (line 14)
@lru_cache(maxsize=1)
def load_tool_snapshot() -> tuple[PortingModule, ...]:
    raw_entries = json.loads(SNAPSHOT_PATH.read_text())
    return tuple(
        PortingModule(
            name=entry['name'],
            responsibility=entry['responsibility'],
            source_hint=entry['source_hint'],
            status='mirrored',  # All loaded as 'mirrored'
        )
        for entry in raw_entries
    )

# Snapshot path derived from module location (line 9)
SNAPSHOT_PATH = Path(__file__).resolve().parent / 'reference_data' / 'tools_snapshot.json'

# Case-insensitive exact lookup (lines 37-40)
needle = name.lower()
for module in PORTED_TOOLS:
    if module.name.lower() == needle:
        return module

# Fuzzy search via substring match (lines 47-49)
matches = [
    module for module in PORTED_TOOLS
    if needle in module.name.lower() or needle in module.source_hint.lower()
]
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **LRU-cached JSON snapshots** — SeekR could cache evolution patterns this way
2. **Snapshot-as-source-of-truth** — Reference data in JSON, loaded at startup
3. **Global singleton via module-level variable** — PORTED_TOOLS is effectively a singleton registry

**缺陷/限制**:
1. Snapshot path is hardcoded relative to `__file__`
2. No reload mechanism if snapshot changes
3. No validation of snapshot schema

---

### 7. `commands.py`

**行数**: 62

**核心类/函数**:
- `load_command_snapshot()` (line 14) — LRU-cached JSON loading
- `PORTED_COMMANDS` (line 27) — Global tuple registry
- `build_command_backlog()` (line 30) — Creates PortingBacklog
- `command_names()`, `get_command()`, `find_commands()`, `render_command_index()` — Same patterns as tools.py

**关键实现模式**: Identical structure to `tools.py` — see above.

**可借鉴点（对 SeekR 的进化机制）**:
1. **Command/Tool duality** — Separating "commands" (user-facing) from "tools" (internal) could map to SeekR's "evolutions" vs "audits"

**缺陷/限制**: Same as tools.py

---

### 8. `port_manifest.py`

**行数**: 53

**核心类/函数**:
- `PortManifest` (line 11) — Workspace manifest frozen dataclass
- `build_port_manifest(src_root)` (line 26) — Scans directory and builds manifest

**关键实现模式**:
```python
# Directory scanning with Counter (lines 28-32)
files = [path for path in root.rglob('*.py') if path.is_file()]
counter = Counter(
    path.relative_to(root).parts[0] if len(path.relative_to(root).parts) > 1 else path.name
    for path in files
    if path.name != '__pycache__'
)

# Hardcoded module notes (lines 34-43)
notes = {
    '__init__.py': 'package export surface',
    'main.py': 'CLI entrypoint',
    'port_manifest.py': 'workspace manifest generation',
    # ...
}

# Top-level modules extracted by first path segment (lines 44-47)
modules = tuple(
    Subsystem(name=name, path=f'src/{name}', file_count=count, notes=notes.get(name, '...'))
    for name, count in counter.most_common()
)
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Manifest generation** — SeekR should be able to generate a manifest of its current capabilities
2. **File counting per subsystem** — Track complexity by file count
3. **Counter.most_common()** — Prioritize by activity/volume

**缺陷/限制**:
1. Hardcoded notes dictionary — not extensible
2. Only top-level modules — no deep hierarchy
3. No cache invalidation if files change

---

### 9. `task.py`

**行数**: 6

**核心类/函数**:
- `PortingTask` — Re-exported from `.task` module

**关键实现模式**:
```python
from .task import PortingTask
__all__ = ['PortingTask']
```

**可借鉴点（对 SeekR 的进化机制）**:
1. Task abstraction could represent "evolution tasks" or "audit tasks"

---

### 10. `tasks.py`

**行数**: 14

**核心类/函数**:
- `default_tasks()` (line 7) — Returns list of default `PortingTask` instances

**关键实现模式**:
```python
def default_tasks() -> list[PortingTask]:
    return [
        PortingTask('root-module-parity', 'Mirror the root module surface...'),
        PortingTask('directory-parity', 'Mirror top-level subsystem names...'),
        PortingTask('parity-audit', 'Continuously measure parity...'),
    ]
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Task registration pattern** — SeekR could have a registry of "evolution tasks"
2. **Default task list** — Provides sane defaults for new workspaces

---

### 11. `query_engine.py`

**行数**: 27

**核心类/函数**:
- `QueryEnginePort` (line 8) — Query engine dataclass
- `from_workspace()` (line 12) — Class method factory
- `render_summary()` (line 15) — Generates Markdown summary

**关键实现模式**:
```python
@dataclass
class QueryEnginePort:
    manifest: PortManifest  # Composition: embeds PortManifest

    @classmethod
    def from_workspace(cls) -> 'QueryEnginePort':
        return cls(manifest=build_port_manifest())

    def render_summary(self) -> str:
        # Builds summary string from multiple components
        sections = [
            '# Python Porting Workspace Summary',
            '',
            self.manifest.to_markdown(),
            '',
            f'{command_backlog.title}: {len(PORTED_COMMANDS)} mirrored entries',
            # ...
        ]
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Summary generation** — SeekR should generate evolution summaries
2. **Composition over inheritance** — PortManifest is composed into QueryEnginePort
3. **Class method factory** — `from_workspace()` pattern for initialization

---

### 12. `context.py`

**行数**: 17

**核心类/函数**:
- `PortContext` (line 8) — Frozen dataclass holding workspace paths
- `build_port_context(base)` (line 13) — Factory function

**关键实现模式**:
```python
@dataclass(frozen=True)
class PortContext:
    source_root: Path
    tests_root: Path
    assets_root: Path

def build_port_context(base: Path | None = None) -> PortContext:
    root = base or Path(__file__).resolve().parent.parent
    return PortContext(
        source_root=root / 'src',
        tests_root=root / 'tests',
        assets_root=root / 'assets'
    )
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Path context management** — SeekR needs to track source/tests/assets roots for the target project
2. **Optional base override** — Allows flexibility for testing

---

### 13. `setup.py`

**行数**: 8

**核心类/函数**:
- `WorkspaceSetup` (line 6) — Frozen dataclass with version and test command

**关键实现模式**:
```python
@dataclass(frozen=True)
class WorkspaceSetup:
    python_version: str = '3.13+'
    test_command: str = 'python3 -m unittest discover -s tests -v'
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Workspace configuration** — SeekR should have workspace setup info

---

### 14. `main.py`

**行数**: 110

**核心类/函数**:
- `build_parser()` (line 10) — Argparse setup with subcommands
- `main(argv)` (line 48) — CLI entry point

**关键实现模式**:
```python
# Subcommand pattern (lines 11-47)
subparsers = parser.add_subparsers(dest='command', required=True)
subparsers.add_parser('summary', help='...')
subparsers.add_parser('manifest', help='...')
subparsers.add_parser('parity-audit', help='...')
route_parser = subparsers.add_parser('route', help='...')
route_parser.add_argument('prompt')
route_parser.add_argument('--limit', type=int, default=5)

# Command dispatch (lines 58-102)
if args.command == 'summary':
    print(QueryEnginePort(manifest).render_summary())
    return 0
elif args.command == 'route':
    matches = PortRuntime().route_prompt(args.prompt, limit=args.limit)
    # ...
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **CLI with subcommands** — SeekR could have `seekr evolve`, `seekr audit`, `seekr status`
2. **Consistent return codes** — 0 for success, 1 for not found, 2 for unknown command

---

### 15. `Tool.py`

**行数**: 16

**核心类/函数**:
- `ToolDefinition` (line 8) — Frozen dataclass for tool metadata
- `DEFAULT_TOOLS` (line 13) — Registry tuple

**关键实现模式**:
```python
DEFAULT_TOOLS = (
    ToolDefinition('port_manifest', 'Summarize the active Python workspace'),
    ToolDefinition('query_engine', 'Render a Python-first porting summary'),
)
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Tool definition registry** — SeekR could define "evolution tools" this way

---

### 16. `query.py`

**行数**: 15

**核心类/函数**:
- `QueryRequest` (line 8) — Frozen request dataclass
- `QueryResponse` (line 12) — Frozen response dataclass

**关键实现模式**:
```python
@dataclass(frozen=True)
class QueryRequest:
    prompt: str

@dataclass(frozen=True)
class QueryResponse:
    text: str
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Request/Response pair** — SeekR could use this for evolution requests

---

### 17. `costHook.py`

**行数**: 10

**核心类/函数**:
- `apply_cost_hook()` (line 7) — Hook function that records cost

**关键实现模式**:
```python
def apply_cost_hook(tracker: CostTracker, label: str, units: int) -> CostTracker:
    tracker.record(label, units)
    return tracker  # Returns tracker for chaining
```

**可借鉴点（对 SeekR 的进化机制）**:
1. **Hook pattern** — Allows cost tracking at various points
2. **Chainable** — Returns tracker for method chaining

---

### 18. `ink.py`

**行数**: 9

**核心类/函数**:
- `render_markdown_panel()` (line 6) — Simple Markdown rendering

**关键实现模式**:
```python
def render_markdown_panel(text: str) -> str:
    border = '=' * 40
    return f"{border}\n{text}\n{border}"
```

**可借鉴点（对 SeekR 的进化机制）**:
1. Output formatting utilities for reports

---

### 19. `interactiveHelpers.py`

**行数**: 9

**核心类/函数**:
- `bulletize()` (line 6) — Converts list to bullet points

**关键实现模式**:
```python
def bulletize(items: list[str]) -> str:
    return '\n'.join(f'- {item}' for item in items)
```

---

### 20. `dialogLaunchers.py`

**行数**: 11

**核心类/函数**:
- `DialogLauncher` (line 8) — Frozen dataclass
- `DEFAULT_DIALOGS` (line 13) — Registry tuple

**关键实现模式**:
```python
DEFAULT_DIALOGS = (
    DialogLauncher('summary', 'Launch the Markdown summary view'),
    DialogLauncher('parity_audit', 'Launch the parity audit view'),
)
```

---

### 21. `replLauncher.py`

**行数**: 8

**核心类/函数**:
- `build_repl_banner()` (line 6) — Returns banner string

**关键实现模式**:
```python
def build_repl_banner() -> str:
    return 'Python porting REPL is not interactive yet; use `python3 -m src.main summary` instead.'
```

---

### 22. `projectOnboardingState.py`

**行数**: 9

**核心类/函数**:
- `ProjectOnboardingState` (line 6) — Project state tracking

**关键实现模式**:
```python
@dataclass
class ProjectOnboardingState:
    has_readme: bool
    has_tests: bool
    python_first: bool = True
```

---

### 23. `__init__.py`

**行数**: 23

**核心类/函数**:
- Package-level exports

**关键实现模式**:
```python
__all__ = [
    'ParityAuditResult',
    'PortManifest',
    'QueryEnginePort',
    'PORTED_COMMANDS',
    'PORTED_TOOLS',
    'build_command_backlog',
    'build_port_manifest',
    'build_tool_backlog',
    'run_parity_audit',
]
```

---

## 跨文件架构模式

### 1. Snapshot 机制

**生成**:
- TypeScript source is analyzed and saved as JSON snapshots in `reference_data/`
- Files: `commands_snapshot.json`, `tools_snapshot.json`, `archive_surface_snapshot.json`

**存储**:
```python
SNAPSHOT_PATH = Path(__file__).resolve().parent / 'reference_data' / 'commands_snapshot.json'
```

**加载**:
```python
@lru_cache(maxsize=1)
def load_command_snapshot() -> tuple[PortingModule, ...]:
    raw_entries = json.loads(SNAPSHOT_PATH.read_text())
    return tuple(PortingModule(...) for entry in raw_entries)
```

**加载时机**: Module import time (eager loading)
**缓存**: LRU cache with maxsize=1 ensures single instance

### 2. Parity Audit 覆盖率计算

```python
# 5个维度:
root_file_coverage = (len(root_hits), len(ARCHIVE_ROOT_FILES))
directory_coverage = (len(dir_hits), len(ARCHIVE_DIR_MAPPINGS))
total_file_ratio = (current_python_files, int(reference['total_ts_like_files']))
command_entry_ratio = (snapshot_count(COMMAND_SNAPSHOT_PATH), int(reference['command_entry_count']))
tool_entry_ratio = (snapshot_count(TOOL_SNAPSHOT_PATH), int(reference['tool_entry_count']))

# 覆盖率 = actual / expected
```

### 3. 反馈闭环 / 自我调整机制

**当前状态**: **没有**显式的反馈闭环机制。

- `route_prompt()` 使用静态评分，不根据选择结果调整
- `run_parity_audit()` 只报告差距，不自动修复
- 没有跟踪 "哪些路由被选择 + 是否成功" 的机制

### 4. 错误处理和降级逻辑

- `get_command(name)` / `get_tool(name)`: 找不到返回 `None`
- `main.py` 中的命令处理: 使用 if-elif 链，未知命令返回 error code 2
- 没有 try-except 包装 file I/O 操作

### 5. 数据流总览

```
JSON Snapshots (reference_data/)
       ↓ (load_*_snapshot with LRU cache)
PORTED_COMMANDS / PORTED_TOOLS (global tuples)
       ↓
PortRuntime.route_prompt() ← User prompt
       ↓
List[RoutedMatch] (ranked by score)
       ↓
main.py dispatch → output
```

---

## 对 SeekR 进化机制的借鉴建议

### 1. Snapshot Pattern → Evolution Pattern Store

CLAWD-CODE uses snapshots to mirror TypeScript → Python. SeekR could:

```python
# Evolution patterns stored as JSON snapshots
EVOLUTION_PATTERNS = load_evolution_snapshot()

# Snapshot structure
{
  "patterns": [
    {
      "id": "error-handling",
      "name": "Error Handling Enhancement",
      "source_hint": "from CLAWD-CODE parity_audit.py",
      "implementation": "def enhance_error_handling(target): ..."
    }
  ]
}
```

### 2. Parity Audit → Capability Gap Analysis

```python
@dataclass(frozen=True)
class EvolutionAuditResult:
    current_capabilities: tuple[str, ...]
    target_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    evolution_suggestions: tuple[str, ...]
```

### 3. Token Routing → Evolution Intent Detection

Replace command/tool routing with evolution intent detection:

```python
def route_evolution_intent(prompt: str) -> list[EvolutionMatch]:
    tokens = tokenize(prompt)
    by_type = {
        'improve': find_improvements(tokens),
        'audit': find_audit_targets(tokens),
        'evolve': find_evolution_opportunities(tokens),
    }
    # Prefer one from each type, then fill remaining slots
```

### 4. Feedback Loop Design

CLAWD-CODE lacks feedback. SeekR should implement:

```python
@dataclass
class EvolutionHistory:
    events: list[EvolutionEvent] = field(default_factory=list)

    def record(self, pattern_id: str, target: str, outcome: str):
        # Track: pattern used → target applied → success/failure
        self.events.append(EvolutionEvent(pattern_id, target, outcome))

# Score adjustment based on history
def score_with_feedback(pattern: EvolutionPattern, history: EvolutionHistory) -> float:
    base_score = pattern.base_score
    historical_success = history.get_success_rate(pattern.id)
    return base_score * historical_success
```

### 5. Cost Tracking → Evolution Cost Model

```python
@dataclass
class EvolutionCostTracker:
    total_cost: float = 0.0
    per_pattern_cost: dict[str, float] = field(default_factory=dict)
    per_target_cost: dict[str, float] = field(default_factory=dict)

    def record(self, pattern_id: str, target: str, cost: float):
        self.total_cost += cost
        self.per_pattern_cost[pattern_id] = self.per_pattern_cost.get(pattern_id, 0) + cost
        self.per_target_cost[target] = self.per_target_cost.get(target, 0) + cost
```

---

## 总结

| 维度 | CLAWD-CODE | SeekR 借鉴方向 |
|------|-----------|---------------|
| 架构风格 | Snapshot-based mirroring | Evolution pattern store |
| 核心机制 | Parity audit | Capability gap analysis |
| 路由 | Token scoring | Intent detection |
| 数据载体 | JSON snapshots + dataclasses | Pattern registry + audit results |
| 反馈闭环 | **无** | 需要设计: 追踪选择→结果→调整分数 |
| 错误处理 | 简单返回 None | 需要更健壮的降级 |
| 持久化 | JSON 文件 | 需要数据库/版本化存储 |

CLAWD-CODE 是一个**静态镜像系统**，而 SeekR 需要的是一个**动态进化系统**。核心区别在于：CLAWD-CODE 映射 "是什么"，SeekR 需要映射 "如何改进"。
