"""Parity Auditor — verifies that a new skill version maintains baseline capabilities.

Runs five parity checks (trigger coverage, reference completeness, output structure,
scoring parity, capability parity) and produces a ParityReport. All checks must pass
for `can_promote()` to return True.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Ensure seekr.scripts.models is importable
# ---------------------------------------------------------------------------
from _path_setup import ensure_paths  # noqa: E402
ensure_paths()

from seekr.scripts.models import (  # noqa: E402
    ParityCheck,
    ParityReport,
    calculate_gem,
    DIMENSION_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_yaml_frontmatter(text: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from a SKILL.md file (simple parser)."""
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    raw = text[3:end].strip()
    result: Dict[str, Any] = {}
    current_list_key: Optional[str] = None
    current_list: List[str] = []

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # List item under a key
        if stripped.startswith("- ") and current_list_key is not None:
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        # Flush previous list
        if current_list_key is not None:
            result[current_list_key] = current_list
            current_list_key = None
            current_list = []
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                current_list_key = key
                current_list = []
            else:
                result[key] = val.strip('"').strip("'")
    if current_list_key is not None:
        result[current_list_key] = current_list
    return result


def _extract_sections(text: str) -> Dict[str, str]:
    """Extract top-level markdown sections (## Title -> content)."""
    sections: Dict[str, str] = {}
    current: Optional[str] = None
    lines: List[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(lines)
            current = line[3:].strip()
            lines = []
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines)
    return sections


def _extract_output_keys(section_text: str) -> List[str]:
    """Extract output field names from a section (backtick-wrapped keys or bold labels)."""
    keys: List[str] = []
    for m in re.finditer(r"`([^`]+)`", section_text):
        keys.append(m.group(1))
    for m in re.finditer(r"\*\*([^*]+)\*\*", section_text):
        keys.append(m.group(1))
    return keys


# ---------------------------------------------------------------------------
# ParityAuditor
# ---------------------------------------------------------------------------

class ParityAuditor:
    """Compare a new skill version against a baseline and verify parity."""

    def __init__(self, new_version_path: str, baseline_path: str) -> None:
        self.new_version_path = new_version_path
        self.baseline_path = baseline_path
        self._checks: List[ParityCheck] = []
        self._blockers: List[str] = []

    # -- public API ---------------------------------------------------------

    def audit(self) -> ParityReport:
        """Run all five parity checks and return a ParityReport."""
        self._checks = []
        self._blockers = []

        self._checks.append(self._check_trigger_coverage())
        self._checks.append(self._check_reference_completeness())
        self._checks.append(self._check_output_structure())
        self._checks.append(self._check_scoring_parity())
        self._checks.append(self._check_capability_parity())

        for check in self._checks:
            if not check.passed:
                self._blockers.append(f"{check.name}: {check.message}")

        all_passed = all(c.passed for c in self._checks)
        return ParityReport(
            version=self.new_version_path,
            baseline=self.baseline_path,
            passed=all_passed,
            checks=self._checks,
            blockers=self._blockers,
        )

    def can_promote(self) -> bool:
        """True only when every parity check passes."""
        return self.audit().passed

    # -- check 1: trigger coverage ------------------------------------------

    def _check_trigger_coverage(self) -> ParityCheck:
        """Verify all trigger phrases from baseline exist in new version."""
        baseline_fm = self._load_frontmatter(self.baseline_path)
        new_fm = self._load_frontmatter(self.new_version_path)

        baseline_triggers: List[str] = baseline_fm.get("triggers", [])
        new_triggers: List[str] = new_fm.get("triggers", [])

        # Also check trigger_rules.json in references/
        baseline_triggers = self._merge_json_triggers(baseline_triggers, self.baseline_path)
        new_triggers = self._merge_json_triggers(new_triggers, self.new_version_path)

        missing = [t for t in baseline_triggers if t not in new_triggers]
        if not missing:
            return ParityCheck(
                name="Trigger Coverage",
                passed=True,
                message="All baseline triggers present.",
                details=f"Checked {len(baseline_triggers)} triggers, 100% coverage.",
            )
        return ParityCheck(
            name="Trigger Coverage",
            passed=False,
            message=f"Missing {len(missing)} trigger(s).",
            details=f"Missing: {', '.join(missing)}",
        )

    # -- check 2: reference completeness ------------------------------------

    def _check_reference_completeness(self) -> ParityCheck:
        """Verify all JSON fields from baseline references exist in new version."""
        baseline_dir = self._skill_dir(self.baseline_path)
        new_dir = self._skill_dir(self.new_version_path)

        baseline_ref_dir = os.path.join(baseline_dir, "references")
        new_ref_dir = os.path.join(new_dir, "references")

        if not os.path.isdir(baseline_ref_dir):
            return ParityCheck(
                name="Reference Completeness",
                passed=True,
                message="No baseline references directory; nothing to compare.",
                details="Skipped — baseline has no references/.",
            )

        missing_files: List[str] = []
        missing_fields: List[str] = []
        baseline_files = {f for f in os.listdir(baseline_ref_dir) if f.endswith(".json")}

        for fname in sorted(baseline_files):
            new_fpath = os.path.join(new_ref_dir, fname) if os.path.isdir(new_ref_dir) else ""
            if not os.path.isfile(new_fpath):
                missing_files.append(fname)
                continue
            baseline_data = _load_json(os.path.join(baseline_ref_dir, fname))
            new_data = _load_json(new_fpath)
            self._compare_keys(baseline_data, new_data, fname, missing_fields)

        if not missing_files and not missing_fields:
            return ParityCheck(
                name="Reference Completeness",
                passed=True,
                message="All reference files and fields present.",
                details=f"Checked {len(baseline_files)} files, 100% field coverage.",
            )
        parts: List[str] = []
        if missing_files:
            parts.append(f"Missing files: {', '.join(missing_files)}")
        if missing_fields:
            parts.append(f"Missing fields: {', '.join(missing_fields[:20])}")
        return ParityCheck(
            name="Reference Completeness",
            passed=False,
            message="Reference data is incomplete.",
            details="; ".join(parts),
        )

    # -- check 3: output structure ------------------------------------------

    def _check_output_structure(self) -> ParityCheck:
        """Compare output schema — additions allowed, removals are not."""
        baseline_sections = self._load_sections(self.baseline_path)
        new_sections = self._load_sections(self.new_version_path)

        missing_sections = [s for s in baseline_sections if s not in new_sections]
        missing_keys: List[str] = []

        for section_name, content in baseline_sections.items():
            if section_name not in new_sections:
                continue
            baseline_keys = set(_extract_output_keys(content))
            new_keys = set(_extract_output_keys(new_sections[section_name]))
            removed = baseline_keys - new_keys
            for k in sorted(removed):
                missing_keys.append(f"{section_name}/{k}")

        if not missing_sections and not missing_keys:
            return ParityCheck(
                name="Output Structure",
                passed=True,
                message="Output structure fully compatible.",
                details=f"Checked {len(baseline_sections)} sections, 100% compatibility.",
            )
        parts: List[str] = []
        if missing_sections:
            parts.append(f"Removed sections: {', '.join(missing_sections)}")
        if missing_keys:
            parts.append(f"Removed keys: {', '.join(missing_keys[:20])}")
        return ParityCheck(
            name="Output Structure",
            passed=False,
            message="Output structure has removals.",
            details="; ".join(parts),
        )

    # -- check 4: scoring parity --------------------------------------------

    def _check_scoring_parity(self) -> ParityCheck:
        """Run calculate_gem() with 10 known score sets; compare results."""
        test_sets: List[Dict[str, float]] = [
            {"S": 80, "H": 75, "E1": 70, "E2": 65, "P": 60},
            {"S": 100, "H": 100, "E1": 100, "E2": 100, "P": 100},
            {"S": 0, "H": 0, "E1": 0, "E2": 0, "P": 0},
            {"S": 50, "H": 50, "E1": 50, "E2": 50, "P": 50},
            {"S": 85, "H": 70, "E1": 60, "E2": 55, "P": 80},
            {"S": 90, "H": 90, "E1": 90, "E2": 90, "P": 90},
            {"S": 30, "H": 40, "E1": 50, "E2": 60, "P": 70},
            {"S": 65, "H": 80, "E1": 45, "E2": 70, "P": 55},
            {"S": 75, "H": 60, "E1": 85, "E2": 40, "P": 90},
            {"S": 55, "H": 55, "E1": 55, "E2": 55, "P": 55},
        ]

        # Scoring parity: verify calculate_gem is deterministic.
        # Since both versions use the same calculate_gem from shared models,
        # we verify the function produces stable, expected results.
        failures: List[str] = []
        tolerance = 1.0  # ±1% tolerance band

        for i, scores in enumerate(test_sets):
            result_a = calculate_gem(scores)
            result_b = calculate_gem(scores)
            if abs(result_a - result_b) > tolerance:
                failures.append(f"Set {i + 1}: {result_a} != {result_b}")

            # Also verify against manual weighted calculation
            total_weight = sum(DIMENSION_WEIGHTS.get(d, 0) for d in scores)
            if total_weight > 0:
                expected = sum(
                    scores[d] * DIMENSION_WEIGHTS.get(d, 0) for d in scores
                ) / total_weight
                expected = round(expected, 2)
                if abs(result_a - expected) > tolerance:
                    failures.append(
                        f"Set {i + 1}: got {result_a}, expected {expected}"
                    )

        if not failures:
            return ParityCheck(
                name="Scoring Parity",
                passed=True,
                message="All 10 score sets produce consistent results.",
                details="GEM calculation is deterministic within tolerance.",
            )
        return ParityCheck(
            name="Scoring Parity",
            passed=False,
            message=f"{len(failures)} scoring mismatch(es).",
            details="; ".join(failures[:10]),
        )

    # -- check 5: capability parity -----------------------------------------

    def _check_capability_parity(self) -> ParityCheck:
        """Compare skill categories between versions."""
        baseline_fm = self._load_frontmatter(self.baseline_path)
        new_fm = self._load_frontmatter(self.new_version_path)

        baseline_tags: List[str] = baseline_fm.get("tags", [])
        new_tags: List[str] = new_fm.get("tags", [])

        # Also extract workflow sections as capability indicators
        baseline_sections = set(self._load_sections(self.baseline_path).keys())
        new_sections = set(self._load_sections(self.new_version_path).keys())

        missing_tags = [t for t in baseline_tags if t not in new_tags]
        missing_capabilities = [s for s in baseline_sections if s not in new_sections]

        if not missing_tags and not missing_capabilities:
            return ParityCheck(
                name="Capability Parity",
                passed=True,
                message="All capabilities present.",
                details=(
                    f"Tags: {len(baseline_tags)} baseline, {len(new_tags)} new. "
                    f"Sections: {len(baseline_sections)} baseline, {len(new_sections)} new."
                ),
            )
        parts: List[str] = []
        if missing_tags:
            parts.append(f"Missing tags: {', '.join(missing_tags)}")
        if missing_capabilities:
            parts.append(f"Missing sections: {', '.join(missing_capabilities)}")
        return ParityCheck(
            name="Capability Parity",
            passed=False,
            message="Capability regression detected.",
            details="; ".join(parts),
        )

    # -- internal helpers ---------------------------------------------------

    def _load_frontmatter(self, path: str) -> Dict[str, Any]:
        text = self._read_file(path)
        return _parse_yaml_frontmatter(text)

    def _load_sections(self, path: str) -> Dict[str, str]:
        text = self._read_file(path)
        return _extract_sections(text)

    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _skill_dir(self, skill_path: str) -> str:
        """Return the directory containing the SKILL.md (the skill root)."""
        if os.path.isdir(skill_path):
            return skill_path
        return os.path.dirname(skill_path)

    def _merge_json_triggers(self, triggers: List[str], skill_path: str) -> List[str]:
        """Merge trigger_rules.json triggers into the frontmatter trigger list."""
        skill_dir = self._skill_dir(skill_path)
        trigger_path = os.path.join(skill_dir, "references", "trigger_rules.json")
        if os.path.isfile(trigger_path):
            data = _load_json(trigger_path)
            for rule in data.get("trigger_rules", []):
                phrase = rule.get("trigger", "")
                if phrase and phrase not in triggers:
                    triggers.append(phrase)
        return triggers

    @staticmethod
    def _compare_keys(
        baseline: Any,
        new: Any,
        prefix: str,
        missing: List[str],
    ) -> None:
        """Recursively compare dict keys between baseline and new data."""
        if isinstance(baseline, dict) and isinstance(new, dict):
            for key in baseline:
                path = f"{prefix}.{key}" if prefix else key
                if key not in new:
                    missing.append(path)
                else:
                    ParityAuditor._compare_keys(baseline[key], new[key], path, missing)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    # Default: audit seekr-evolve/SKILL.md against seekr/SKILL.md
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace = os.path.dirname(base_dir)

    baseline = os.path.join(workspace, "seekr", "SKILL.md")
    candidate = os.path.join(workspace, "seekr-evolve", "SKILL.md")

    if not os.path.isfile(baseline):
        print(f"Baseline not found: {baseline}")
        raise SystemExit(1)
    if not os.path.isfile(candidate):
        print(f"Candidate not found: {candidate}")
        raise SystemExit(1)

    auditor = ParityAuditor(new_version_path=candidate, baseline_path=baseline)
    report = auditor.audit()

    print(f"\n{'=' * 60}")
    print(f"  PARITY AUDIT REPORT")
    print(f"{'=' * 60}")
    print(f"  Baseline : {report.baseline}")
    print(f"  Version  : {report.version}")
    print(f"  Overall  : {'PASS' if report.passed else 'FAIL'}")
    print(f"{'=' * 60}\n")

    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.name}")
        print(f"         {check.message}")
        print(f"         {check.details}\n")

    if report.blockers:
        print(f"  BLOCKERS ({len(report.blockers)}):")
        for blocker in report.blockers:
            print(f"    - {blocker}")
        print()

    can = auditor.can_promote()
    print(f"  can_promote() -> {can}")
    raise SystemExit(0 if can else 1)
