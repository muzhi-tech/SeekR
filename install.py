#!/usr/bin/env python3
"""
SeekR Skill Dependency Installer & Configuration Manager

Usage:
    python install.py                    # Check & report missing skills
    python install.py --install          # Check & auto-install missing skills
    python install.py --force            # Re-install all skills
    python install.py --workflow A       # Only check skills for Workflow A
    python install.py init               # Interactive config setup
    python install.py validate           # Validate config and dependencies
    python install.py --list             # List workflows and their skills
    python install.py --status           # Show overall installation status
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

REGISTRY_PATH = Path(__file__).parent / "SKILLS-REGISTRY.json"
SEEKR_DIR = Path(__file__).parent
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"
CLAUDE_AGENTS_DIR = Path.home() / ".claude" / "agents"
CONFIG_PATH = SEEKR_DIR / "config.yaml"
CONFIG_EXAMPLE_PATH = SEEKR_DIR / "config.yaml.example"

# 本地技能源（按优先级搜索）
LOCAL_SOURCES = [
    SEEKR_DIR / "Openclaw参考",
    SEEKR_DIR.parent / "geo-seo-openclaw-skills" / "skills",
]

# Workflow -> 所需 skill_ids
WORKFLOW_SKILLS: Dict[str, List[str]] = {
    "A": [
        "seo-audit", "seo-technical", "seo-content", "seo-schema",
        "seo-competitor-pages", "geo-audit", "geo-ai-visibility",
        "geo-brand-mentions", "geo-schema", "geo-technical",
        "geo-content", "geo-platform-analysis", "backlink-analyzer",
        "domain-authority-auditor", "geo-report", "geo-report-pdf",
        "seo-sitemap", "seo-local", "seo-maps",
    ],
    "B": [
        "seo-technical", "seo-content", "seo-schema",
        "keyword-research", "serp-analysis", "content-gap-analysis",
        "meta-tags-optimizer", "internal-linking-optimizer",
        "seo-page",
    ],
    "C": [
        "seo-geo-analyzer", "geo-citability", "geo-brand-mentions",
        "geo-platform-optimizer", "geo-schema", "geo-content",
        "geo-technical", "geo-report", "geo-report-pdf",
        "geo-llmstxt", "geo-crawlers",
    ],
    "D": [
        "keyword-research", "serp-analysis", "content-gap-analysis",
        "seo-content-writer", "geo-content-optimizer",
        "schema-markup-generator", "seo-content", "seo-schema",
        "meta-tags-optimizer", "rank-tracker",
    ],
}

WORKFLOW_NAMES: Dict[str, str] = {
    "A": "Full SEO+GEO Audit",
    "B": "Keyword Optimization",
    "C": "GEO Visibility Plan",
    "D": "GEO Article Generation",
}

# Agent-type 技能（单 .md 文件在 ~/.claude/agents/）
AGENT_SKILLS: Dict[str, str] = {
    "geo-ai-visibility": "geo-ai-visibility.md",
    "geo-schema": "geo-schema.md",
    "geo-technical": "geo-technical.md",
    "geo-content": "geo-content.md",
    "geo-platform-analysis": "geo-platform-analysis.md",
}

# Subagent-type 技能（单 .md 文件在子目录）
SUBAGENT_SKILLS: Dict[str, str] = {
    "seo-technical": "seo/agents/seo-technical.md",
    "seo-content": "seo/agents/seo-content.md",
    "seo-schema": "seo/agents/seo-schema.md",
}

# 验证所需的 Python 脚本和 JSON 参考文件
REQUIRED_SCRIPTS = [
    "seekr/scripts/llm_dispatcher.py",
    "seekr/scripts/models.py",
    "seekr/scripts/sheep_scorer.py",
]

REQUIRED_REFERENCES = [
    "seekr/references/platforms.json",
    "seekr/references/sheep_thresholds.json",
    "seekr/references/trigger_rules.json",
    "seekr/references/llm_defaults.json",
]


# ===================================================================
# 通用工具函数
# ===================================================================

def load_registry() -> dict:
    """加载 SKILLS-REGISTRY.json"""
    if not REGISTRY_PATH.exists():
        print(f"[ERROR] Registry not found: {REGISTRY_PATH}")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_skill_location(skill_id: str, registry: dict) -> Optional[Path]:
    """获取技能在文件系统上的预期路径"""
    if skill_id in AGENT_SKILLS:
        return CLAUDE_AGENTS_DIR / AGENT_SKILLS[skill_id]
    if skill_id in SUBAGENT_SKILLS:
        return CLAUDE_SKILLS_DIR / SUBAGENT_SKILLS[skill_id]
    return CLAUDE_SKILLS_DIR / skill_id


def check_skill(skill_id: str, registry: dict) -> dict:
    """检查技能是否已安装"""
    location = get_skill_location(skill_id, registry)
    if location is None:
        return {"skill_id": skill_id, "status": "unknown", "location": "N/A"}

    if skill_id in AGENT_SKILLS or skill_id in SUBAGENT_SKILLS:
        exists = location.exists() and location.is_file()
    else:
        if location.is_symlink() or location.is_dir():
            has_skill_md = (location / "SKILL.md").exists()
            has_content = any(location.glob("*.md"))
            exists = has_skill_md or has_content
        else:
            exists = False

    return {
        "skill_id": skill_id,
        "status": "installed" if exists else "missing",
        "location": str(location),
    }


def find_local_source(skill_id: str) -> Optional[Path]:
    """在本地目录中查找技能源"""
    for source_dir in LOCAL_SOURCES:
        if not source_dir.exists():
            continue
        direct = source_dir / skill_id
        if direct.exists() and (direct / "SKILL.md").exists():
            return direct
        for item in source_dir.iterdir():
            if item.is_dir() and item.name.startswith(skill_id):
                if (item / "SKILL.md").exists():
                    return item
    return None


def install_skill(skill_id: str, registry: dict) -> bool:
    """尝试安装缺失的技能"""
    location = get_skill_location(skill_id, registry)
    if location is None:
        return False

    if skill_id in AGENT_SKILLS or skill_id in SUBAGENT_SKILLS:
        print(f"  [SKIP] {skill_id} 是 agent-type 技能，需手动安装")
        print(f"         预期位置: {location}")
        return False

    source = find_local_source(skill_id)
    if source:
        location.parent.mkdir(parents=True, exist_ok=True)
        if location.exists():
            if location.is_symlink():
                location.unlink()
            elif location.is_dir():
                shutil.rmtree(location)
        shutil.copytree(source, location)
        print(f"  [INSTALLED] {skill_id} <- {source}")
        return True

    if location.is_symlink():
        target = os.readlink(location)
        print(f"  [SYMLINK] {skill_id} -> {target}")
        if Path(target).exists():
            return True

    print(f"  [MISSING] {skill_id} 在本地源中未找到")
    print(f"            尝试: claude /find-skills {skill_id}")
    return False


def check_all(registry: dict, workflow: Optional[str] = None) -> list:
    """检查所有技能或指定 workflow 的技能"""
    if workflow:
        skill_ids = WORKFLOW_SKILLS.get(workflow.upper(), [])
    else:
        skill_ids = WORKFLOW_SKILLS["A"] + WORKFLOW_SKILLS["B"] + WORKFLOW_SKILLS["C"] + WORKFLOW_SKILLS["D"]
        seen = set()
        unique_ids = []
        for sid in skill_ids:
            if sid not in seen:
                seen.add(sid)
                unique_ids.append(sid)
        skill_ids = unique_ids

    return [check_skill(sid, registry) for sid in skill_ids]


def get_all_unique_skills() -> List[str]:
    """获取所有不重复的技能 ID（保持顺序）"""
    seen = set()
    result = []
    for wf_skills in WORKFLOW_SKILLS.values():
        for sid in wf_skills:
            if sid not in seen:
                seen.add(sid)
                result.append(sid)
    return result


def print_report(results: list, verbose: bool = False) -> int:
    """打印技能状态报告，返回缺失数量"""
    installed = [r for r in results if r["status"] == "installed"]
    missing = [r for r in results if r["status"] == "missing"]

    print(f"\n{'='*60}")
    print(f"  SeekR Skill Dependency Report")
    print(f"{'='*60}")
    print(f"  Total: {len(results)} | Installed: {len(installed)} | Missing: {len(missing)}")
    print(f"{'='*60}\n")

    if missing:
        print("  MISSING SKILLS:")
        for r in missing:
            print(f"    - {r['skill_id']}")
            if verbose:
                print(f"      Expected: {r['location']}")
        print()

    if verbose and installed:
        print("  INSTALLED SKILLS:")
        for r in installed:
            print(f"    + {r['skill_id']}")
        print()

    return len(missing)


# ===================================================================
# config.yaml 读写工具
# ===================================================================

def _parse_simple_yaml(text: str) -> dict:
    """简易 YAML 解析器（仅支持 SeekR 配置的嵌套结构，不引入依赖）"""
    result: dict = {}
    current_path: List[str] = []

    for line in text.splitlines():
        stripped = line.rstrip()

        # 跳过空行和注释
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        # 计算缩进级别
        indent = len(line) - len(line.lstrip())
        content = stripped.strip()

        # 根据缩进调整当前路径层级（每 2 空格为一级）
        level = indent // 2
        current_path = current_path[:level]

        if ":" in content:
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()

            if val == "":
                # 嵌套节点的开始
                current_path.append(key)
            else:
                # 叶子节点 — 去掉引号
                val = val.strip('"').strip("'")
                _set_nested(result, current_path + [key], val)

    return result


def _set_nested(d: dict, path: List[str], value: str) -> None:
    """在嵌套 dict 中设置值"""
    for key in path[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[path[-1]] = value


def _dump_simple_yaml(data: dict, indent: int = 0) -> str:
    """将 dict 序列化为简易 YAML 字符串"""
    lines: List[str] = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dump_simple_yaml(value, indent + 1))
        else:
            # 字符串值加引号，数字和布尔不加
            if isinstance(value, str) and value not in ("true", "false", ""):
                try:
                    float(value)
                except ValueError:
                    value = f'"{value}"'
            lines.append(f"{prefix}{key}: {value}")

    return "\n".join(lines)


def load_config() -> Optional[dict]:
    """加载 config.yaml，返回解析后的 dict 或 None"""
    if not CONFIG_PATH.exists():
        return None
    try:
        text = CONFIG_PATH.read_text(encoding="utf-8")
        return _parse_simple_yaml(text)
    except Exception:
        return None


def save_config(data: dict) -> None:
    """保存配置到 config.yaml"""
    lines = [
        "# SeekR LLM Dispatcher Configuration",
        "# Auto-generated by install.py init",
        "#",
    ]
    lines.append(_dump_simple_yaml(data))
    lines.append("")
    CONFIG_PATH.write_text("\n".join(lines), encoding="utf-8")


# ===================================================================
# 子命令: init（交互式配置）
# ===================================================================

def cmd_init(args: argparse.Namespace) -> None:
    """交互式配置初始化"""
    print()
    print("=" * 55)
    print("  SeekR 配置初始化")
    print("=" * 55)
    print()

    # 1. 检测 config.yaml 是否存在，不存在则从 example 复制
    if CONFIG_PATH.exists():
        print(f"  已存在 config.yaml，将在其基础上更新。")
        config = load_config() or {}
    else:
        if CONFIG_EXAMPLE_PATH.exists():
            shutil.copy2(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
            print(f"  已从 config.yaml.example 创建 config.yaml")
            config = load_config() or {}
        else:
            print("  [WARN] config.yaml.example 未找到，将创建空配置")
            config = {}

    # 确保 providers 和 dispatch 结构存在
    if "providers" not in config:
        config["providers"] = {}
    if "dispatch" not in config:
        config["dispatch"] = {}

    providers = config["providers"]
    if "gemini" not in providers:
        providers["gemini"] = {"api_key": "", "model": "gemini-2.0-flash", "api_base": ""}
    if "claude" not in providers:
        providers["claude"] = {"api_key": "", "model": "claude-sonnet-4-20250514", "api_base": ""}
    if "openai_compatible" not in providers:
        providers["openai_compatible"] = {
            "api_key": "", "model": "deepseek-chat",
            "api_base": "https://api.deepseek.com/v1",
        }

    dispatch = config["dispatch"]
    if "prompt" not in dispatch:
        dispatch["prompt"] = {"provider": "gemini", "temperature": "0.7", "max_tokens": "4096"}
    if "article" not in dispatch:
        dispatch["article"] = {"provider": "claude", "temperature": "0.5", "max_tokens": "8192"}
    if "timeout" not in dispatch:
        dispatch["timeout"] = "120"

    print()
    print("  请输入 API Keys（直接回车跳过）：")
    print()

    # 2. Gemini API key
    current_gemini_key = providers["gemini"].get("api_key", "")
    hint = f" (当前: {current_gemini_key[:8]}...)" if current_gemini_key else ""
    gemini_key = input(f"  Gemini API Key{hint}: ").strip()
    if gemini_key:
        providers["gemini"]["api_key"] = gemini_key
    print()

    # 3. Claude API key
    current_claude_key = providers["claude"].get("api_key", "")
    hint = f" (当前: {current_claude_key[:8]}...)" if current_claude_key else ""
    claude_key = input(f"  Claude API Key{hint}: ").strip()
    if claude_key:
        providers["claude"]["api_key"] = claude_key
    print()

    # 4. OpenAI Compatible
    current_oai_key = providers["openai_compatible"].get("api_key", "")
    hint = f" (当前: {current_oai_key[:8]}...)" if current_oai_key else ""
    oai_key = input(f"  OpenAI Compatible API Key{hint}: ").strip()
    if oai_key:
        providers["openai_compatible"]["api_key"] = oai_key

    current_oai_base = providers["openai_compatible"].get("api_base", "")
    hint = f" (当前: {current_oai_base})" if current_oai_base else ""
    oai_base = input(f"  OpenAI Compatible Base URL{hint}: ").strip()
    if oai_base:
        providers["openai_compatible"]["api_base"] = oai_base
    print()

    # 5. 选择默认 provider
    print("  选择默认 provider：")
    print("    1) gemini   — 用于 prompt 生成（大纲、研究）")
    print("    2) claude   — 用于 GEO 文章生成")
    print("    3) openai_compatible — 用于自定义模型")
    print()

    prompt_default = dispatch["prompt"].get("provider", "gemini")
    choice = input(f"  prompt 默认 provider [{prompt_default}]: ").strip()
    if choice:
        dispatch["prompt"]["provider"] = choice

    article_default = dispatch["article"].get("provider", "claude")
    choice = input(f"  article 默认 provider [{article_default}]: ").strip()
    if choice:
        dispatch["article"]["provider"] = choice

    # 6. 写入配置
    save_config(config)
    print()
    print(f"  配置已保存到 {CONFIG_PATH}")
    print()

    # 7. 自动运行 validate
    print("  正在验证配置...")
    print()
    cmd_validate(args)


# ===================================================================
# 子命令: validate（验证配置和依赖）
# ===================================================================

def cmd_validate(args: argparse.Namespace) -> None:
    """验证配置和依赖完整性"""
    all_ok = True

    # 1. config.yaml 存在性
    print("  [检查] config.yaml")
    if CONFIG_PATH.exists():
        print("    config.yaml 存在")
    else:
        print("    [FAIL] config.yaml 不存在，运行 'python install.py init' 创建")
        all_ok = False

    # 2. 解析 config.yaml，验证 provider key
    if CONFIG_PATH.exists():
        print("  [检查] Provider 配置")
        config = load_config()
        if config is None:
            print("    [FAIL] config.yaml 解析失败")
            all_ok = False
        else:
            providers = config.get("providers", {})
            has_any_key = False
            for pname in ("gemini", "claude", "openai_compatible"):
                pdata = providers.get(pname, {})
                key = pdata.get("api_key", "")
                if key:
                    has_any_key = True
                    print(f"    {pname}: api_key 已配置 ({key[:6]}...)")
                else:
                    print(f"    {pname}: api_key 未设置")

            if not has_any_key:
                print("    [FAIL] 至少需要配置一个 provider 的 API key")
                all_ok = False
            else:
                print("    至少一个 provider 已配置")

        # 3. 验证 dispatch 路由引用的 provider 存在
        if config is not None:
            print("  [检查] Dispatch 路由")
            providers = config.get("providers", {})
            dispatch = config.get("dispatch", {})
            for task in ("prompt", "article"):
                task_cfg = dispatch.get(task, {})
                provider = task_cfg.get("provider", "")
                if provider and provider not in providers:
                    print(f"    [FAIL] dispatch.{task}.provider = '{provider}' 但 providers 中不存在")
                    all_ok = False
                elif provider:
                    print(f"    dispatch.{task} -> {provider}")
                else:
                    print(f"    [WARN] dispatch.{task}.provider 未设置")

    # 4. 验证 Python 脚本
    print("  [检查] Python 脚本")
    for script in REQUIRED_SCRIPTS:
        path = SEEKR_DIR / script
        if path.exists():
            print(f"    {script}")
        else:
            print(f"    [FAIL] {script} 不存在")
            all_ok = False

    # 5. 验证 JSON 参考文件
    print("  [检查] JSON 参考文件")
    for ref in REQUIRED_REFERENCES:
        path = SEEKR_DIR / ref
        if path.exists():
            print(f"    {ref}")
        else:
            print(f"    [FAIL] {ref} 不存在")
            all_ok = False

    # 6. 验证 SKILLS-REGISTRY.json
    print("  [检查] SKILLS-REGISTRY.json")
    if REGISTRY_PATH.exists():
        print(f"    SKILLS-REGISTRY.json 存在")
    else:
        print(f"    [FAIL] SKILLS-REGISTRY.json 不存在")
        all_ok = False

    # 汇总
    print()
    if all_ok:
        print("  验证通过")
    else:
        print("  验证发现问题，请根据上述 [FAIL] 项修复")
    print()


# ===================================================================
# 子命令: --list（列出工作流和技能）
# ===================================================================

def cmd_list(args: argparse.Namespace) -> None:
    """列出所有工作流及其所需技能"""
    registry = load_registry()

    print()
    print("=" * 60)
    print("  SeekR Workflows & Skills")
    print("=" * 60)

    for wf_id in ("A", "B", "C", "D"):
        skills = WORKFLOW_SKILLS[wf_id]
        name = WORKFLOW_NAMES[wf_id]
        print(f"\n  Workflow {wf_id} — {name} ({len(skills)} skills):")

        for sid in skills:
            result = check_skill(sid, registry)
            mark = "+" if result["status"] == "installed" else "-"
            print(f"    [{mark}] {sid}")

    print()


# ===================================================================
# 子命令: --status（安装状态总览）
# ===================================================================

def cmd_status(args: argparse.Namespace) -> None:
    """显示整体安装状态"""
    registry = load_registry()

    # 检查所有技能
    all_skills = get_all_unique_skills()
    results = [check_skill(sid, registry) for sid in all_skills]
    installed = sum(1 for r in results if r["status"] == "installed")
    total = len(results)

    # 检查配置状态
    if CONFIG_PATH.exists():
        config = load_config()
        if config is not None:
            providers = config.get("providers", {})
            has_key = any(
                providers.get(p, {}).get("api_key", "")
                for p in ("gemini", "claude", "openai_compatible")
            )
            config_status = "valid" if has_key else "no keys"
        else:
            config_status = "parse error"
    else:
        config_status = "missing"

    print()
    print(f"  SeekR: {installed}/{total} skills installed, config: {config_status}")
    print()

    # 详细列出每个技能状态
    for r in results:
        mark = "+" if r["status"] == "installed" else "-"
        print(f"    [{mark}] {r['skill_id']}")

    print()


# ===================================================================
# 子命令: 默认（检查 + 可选安装）
# ===================================================================

def cmd_check(args: argparse.Namespace) -> None:
    """检查技能依赖状态，可选安装缺失技能"""
    registry = load_registry()
    workflow = getattr(args, "workflow", None)
    verbose = getattr(args, "verbose", False)
    do_install = getattr(args, "install", False)
    force = getattr(args, "force", False)

    if force:
        print("[FORCE] 重新安装所有技能...")
        results = check_all(registry, workflow)
        for r in results:
            install_skill(r["skill_id"], registry)
        print("\n[FORCE] 重新检查...")
        results = check_all(registry, workflow)
        print_report(results, verbose)
    else:
        results = check_all(registry, workflow)
        missing_count = print_report(results, verbose)

        if missing_count > 0 and do_install:
            print("\n[AUTO-INSTALL] 正在安装缺失技能...\n")
            missing_ids = [r["skill_id"] for r in results if r["status"] == "missing"]
            for sid in missing_ids:
                install_skill(sid, registry)

            print("\n[RE-CHECK] 验证安装结果...\n")
            results = check_all(registry, workflow)
            missing_count = print_report(results, verbose)

            if missing_count > 0:
                print(f"\n[WARN] 仍有 {missing_count} 个技能缺失。")
                print("       运行: claude /find-skills <skill-name> 搜索")
                print("       或从 Openclaw marketplace 手动安装")
        elif missing_count > 0 and not do_install:
            print(f"[HINT] 加 --install 自动安装: python install.py --install")

    print()


# ===================================================================
# argparse 参数解析
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="SeekR Skill Dependency Installer & Configuration Manager",
    )

    # 子命令
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="交互式配置初始化")
    sub.add_parser("validate", help="验证配置和依赖完整性")

    # 全局选项（与旧接口兼容）
    parser.add_argument("--install", action="store_true", help="自动安装缺失技能")
    parser.add_argument("--force", action="store_true", help="强制重新安装所有技能")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--workflow", type=str, help="仅检查指定 workflow 的技能 (A/B/C/D)")
    parser.add_argument("--list", action="store_true", help="列出所有工作流及其技能")
    parser.add_argument("--status", action="store_true", help="显示安装状态总览")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # --list 和 --status 作为标志处理
    if getattr(args, "list", False):
        cmd_list(args)
        return

    if getattr(args, "status", False):
        cmd_status(args)
        return

    # 子命令
    if args.command == "init":
        cmd_init(args)
        return

    if args.command == "validate":
        cmd_validate(args)
        return

    # 默认：检查 + 可选安装
    cmd_check(args)


if __name__ == "__main__":
    main()
