#!/usr/bin/env python3
"""
SeekR Skill Dependency Installer

Reads SKILLS-REGISTRY.json, checks each skill at its expected location,
reports status, and installs missing skills.

Usage:
    python install.py              # Check & report missing skills
    python install.py --install    # Check & auto-install missing skills
    python install.py --force      # Re-install all skills
    python install.py --workflow A # Only check skills for Workflow A
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional


# --- Config ---

REGISTRY_PATH = Path(__file__).parent / "SKILLS-REGISTRY.json"
SEEKR_DIR = Path(__file__).parent
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"
CLAUDE_AGENTS_DIR = Path.home() / ".claude" / "agents"

# Local skill sources to copy from (checked in order)
LOCAL_SOURCES = [
    SEEKR_DIR / "Openclaw参考",
    SEEKR_DIR.parent / "geo-seo-openclaw-skills" / "skills",
]

# Workflow -> required skill_ids mapping (extracted from registry)
WORKFLOW_SKILLS = {
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

# Agent-type skills (single .md file in ~/.claude/agents/)
AGENT_SKILLS = {
    "geo-ai-visibility": "geo-ai-visibility.md",
    "geo-schema": "geo-schema.md",
    "geo-technical": "geo-technical.md",
    "geo-content": "geo-content.md",
    "geo-platform-analysis": "geo-platform-analysis.md",
}

# Subagent-type skills (single .md file in subdirectory)
SUBAGENT_SKILLS = {
    "seo-technical": "seo/agents/seo-technical.md",
    "seo-content": "seo/agents/seo-content.md",
    "seo-schema": "seo/agents/seo-schema.md",
}


def load_registry() -> dict:
    """Load SKILLS-REGISTRY.json."""
    if not REGISTRY_PATH.exists():
        print(f"[ERROR] Registry not found: {REGISTRY_PATH}")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_skill_location(skill_id: str, registry: dict) -> Optional[Path]:
    """Get expected filesystem path for a skill."""
    # Check agent skills first
    if skill_id in AGENT_SKILLS:
        return CLAUDE_AGENTS_DIR / AGENT_SKILLS[skill_id]

    # Check subagent skills
    if skill_id in SUBAGENT_SKILLS:
        return CLAUDE_SKILLS_DIR / SUBAGENT_SKILLS[skill_id]

    # Default: directory skill
    return CLAUDE_SKILLS_DIR / skill_id


def check_skill(skill_id: str, registry: dict) -> dict:
    """Check if a skill is installed. Returns status dict."""
    location = get_skill_location(skill_id, registry)

    if location is None:
        return {"skill_id": skill_id, "status": "unknown", "location": "N/A"}

    if skill_id in AGENT_SKILLS:
        exists = location.exists() and location.is_file()
    elif skill_id in SUBAGENT_SKILLS:
        exists = location.exists() and location.is_file()
    else:
        # Directory skill: check dir exists and has SKILL.md or any .md
        if location.is_symlink() or location.is_dir():
            has_content = any(location.glob("*.md")) or any(location.glob("SKILL.md"))
            has_skill_md = (location / "SKILL.md").exists()
            exists = has_skill_md or has_content
        else:
            exists = False

    return {
        "skill_id": skill_id,
        "status": "installed" if exists else "missing",
        "location": str(location),
    }


def find_local_source(skill_id: str) -> Optional[Path]:
    """Find skill source in local directories."""
    for source_dir in LOCAL_SOURCES:
        if not source_dir.exists():
            continue
        # Check direct match
        direct = source_dir / skill_id
        if direct.exists() and (direct / "SKILL.md").exists():
            return direct
        # Check with version suffix (e.g., geo-content-optimizer-6.2.0)
        for item in source_dir.iterdir():
            if item.is_dir() and item.name.startswith(skill_id):
                if (item / "SKILL.md").exists():
                    return item
    return None


def install_skill(skill_id: str, registry: dict) -> bool:
    """Try to install a missing skill. Returns True on success."""
    location = get_skill_location(skill_id, registry)
    if location is None:
        return False

    # For agent/subagent skills, we can't auto-install
    if skill_id in AGENT_SKILLS or skill_id in SUBAGENT_SKILLS:
        print(f"  [SKIP] {skill_id} is an agent-type skill, requires manual install")
        print(f"         Expected at: {location}")
        return False

    # Try to find and copy from local sources
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

    # Check if it exists as a symlink target
    if location.is_symlink():
        target = os.readlink(location)
        print(f"  [SYMLINK] {skill_id} -> {target}")
        if Path(target).exists():
            return True

    print(f"  [MISSING] {skill_id} not found in local sources")
    print(f"            Try: claude /find-skills {skill_id}")
    return False


def check_all(registry: dict, workflow: Optional[str] = None) -> list:
    """Check all skills or skills for a specific workflow."""
    if workflow:
        skill_ids = WORKFLOW_SKILLS.get(workflow.upper(), [])
    else:
        skill_ids = WORKFLOW_SKILLS["A"] + WORKFLOW_SKILLS["B"] + WORKFLOW_SKILLS["C"] + WORKFLOW_SKILLS["D"]
        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        for sid in skill_ids:
            if sid not in seen:
                seen.add(sid)
                unique_ids.append(sid)
        skill_ids = unique_ids

    results = []
    for sid in skill_ids:
        results.append(check_skill(sid, registry))
    return results


def print_report(results: list, verbose: bool = False):
    """Print a status report."""
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


def main():
    args = sys.argv[1:]
    do_install = "--install" in args or "--force" in args
    force = "--force" in args
    verbose = "--verbose" in args or "-v" in args
    workflow = None

    # Parse --workflow X
    for i, arg in enumerate(args):
        if arg == "--workflow" and i + 1 < len(args):
            workflow = args[i + 1].upper()
            if workflow not in WORKFLOW_SKILLS:
                print(f"[ERROR] Unknown workflow: {workflow}. Use A, B, C, or D.")
                sys.exit(1)

    registry = load_registry()

    if force:
        # Force reinstall: treat all as missing
        print("[FORCE] Re-installing all skills...")
        results = check_all(registry, workflow)
        for r in results:
            install_skill(r["skill_id"], registry)
        print("\n[FORCE] Re-checking...")
        results = check_all(registry, workflow)
        print_report(results, verbose)
    else:
        results = check_all(registry, workflow)
        missing_count = print_report(results, verbose)

        if missing_count > 0 and do_install:
            print("\n[AUTO-INSTALL] Attempting to install missing skills...\n")
            missing_ids = [r["skill_id"] for r in results if r["status"] == "missing"]
            for sid in missing_ids:
                install_skill(sid, registry)

            print("\n[RE-CHECK] Verifying installation...\n")
            results = check_all(registry, workflow)
            missing_count = print_report(results, verbose)

            if missing_count > 0:
                print(f"\n[WARN] {missing_count} skills still missing.")
                print("       Run: claude /find-skills <skill-name> to search")
                print("       Or install manually from Openclaw marketplace")
        elif missing_count > 0 and not do_install:
            print(f"[HINT] Run with --install to auto-install: python install.py --install")

    print()


if __name__ == "__main__":
    main()
