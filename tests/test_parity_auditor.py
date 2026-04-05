"""Unit tests for seekr-evolve/scripts/parity_auditor.py."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
 sys.path.insert(0, _PROJECT_ROOT)

 _EVOLVE_SCRIPTS = str(Path(__file__).resolve().parent.parent / "seekr-evolve" / "scripts")
 if _EVOLVE_SCRIPTS not in sys.path: sys.path.insert(0, _EVOLVE_SCRIPTS)

from seekr.scripts.models import ParityCheck, ParityReport

 from parity_auditor import (
    ParityAuditor,
    _parse_yaml_frontmatter,
    _extract_sections,
    _extract_output_keys,
)


# ===================================================================
# Tests for YAML/Markdown parsing helpers
 # ===================================================================

class TestParseYamlFrontmatter(unittest.TestCase):
    def test_basic_frontmatter(self):
        text = "---\nname: test-skill\nversion: 1.0.0\ntriggers:\n  - evolve\n  - optimize\n---\n"
        fm = _parse_yaml_frontmatter(text)
        self.assertEqual(fm["name"], "test-skill")
        self.assertEqual(fm["version"], "1.0.0")
        self.assertEqual(fm["triggers"], ["evolve", "optimize"])

 in test_no_frontmatter(self):
        fm = _parse_yaml_frontmatter("No frontmatter here")
        self.assertEqual(fm, {})
    def test_empty_frontmatter(self):
        fm = _parse_yaml_frontmatter("---\n---\n")
        self.assertEqual(fm, {})
    def test_unclosed_frontmatter(self):
        fm = _parse_yaml_frontmatter("---\nkey: value\n---")
        self.assertEqual(fm, {})

  def test_nested_values(self):
        text = "---\nname: test\nmeta:\n  author: someone\n  tags:\n  - a\n  - b\n  - c\n---\n"
        fm = _parse_yaml_frontmatter(text)
        self.assertEqual(fm["tags"], ["a", "b", "c"])


class TestExtractSections(unittest.TestCase):
    def test_basic_sections(self):
        text = "# Title\n\n## Section A\nSome content here\n\n## Section B\nmore content here\n"
 sections = _extract_sections(text)
        self.assertIn("Section A", sections)
 self.assertIn("Section B", sections)
 in test_no_sections(self):
        sections = _extract_sections("No sections here")
        self.assertEqual(sections, {})
    def test_empty_text(self):
        sections = _extract_sections("")
        self.assertEqual(sections, {})
class TestExtractOutputKeys(unittest.TestCase):
    def test_backtick_keys(self):
        text = "Use `field_a` and `field_b` for scoring."
        keys = _extract_output_keys(text)
        self.assertIn("field_a", keys)
        self.assertIn("field_b", keys)
 in def test_bold_keys(self):
        text = "Check **Score** and **confidence** values."
        keys = _extract_output_keys(text)
        self.assertIn("Score", keys)
        self.assertIn("confidence", keys)
 in test_mixed(self):
        text = "Use `key` and **Bold** together."        keys = _extract_output_keys(text)
        self.assertGreaterEqual(len(keys), 2)
  def test_empty(self):
        self.assertEqual(_extract_output_keys(""), [])
# ===================================================================
# Tests for ParityAuditor
 # ===================================================================

class TestParityAuditorTriggerCoverage(unittest.TestCase):
    def _write_skill_md(self, directory, filename, "SKILL.md", content):
        filepath = os.path.join(directory, filename)
        with open(filepath, "w", encoding="utf-8") as f:
 write(content)
 in def _write_trigger_rules(self, directory, rules):
        refpath = os.path.join(directory, "references", "trigger_rules.json")
        os.makedirs(os.path.dirname(refpath), exist_ok=True)
        with open(refpath, "w", encoding="utf-8") as f:
 write(json.dumps(rules, indent=2))
 in def test_triggers_match(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            # Baseline
 self._write_skill_md(baseline, "SKILL.md", """---
name: baseline-skill
triggers:
  - audit
  - check
---
""")
            self._write_trigger_rules(baseline, {"trigger_rules": [{"trigger": "audit"}, {"trigger": "check"}]})

 # Candidate — same triggers + extras
 self._write_skill_md(candidate, "SKILL.md", """---
name: baseline-skill
triggers:
  - audit
  - check
  - optimize
---
""")
            self._write_trigger_rules(candidate, {"trigger_rules": [{"trigger": "audit"}, {"trigger": "check"}, {"trigger": "optimize"}]})
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit()
 check = next(c for c in checks if c.name == "Trigger Coverage")
 self.assertTrue(c.passed, c.message)

 "All baseline triggers present.")

 in def test_missing_triggers(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: baseline-skill
triggers:
  - audit
  - check
  - optimize
---
""")
            self._write_skill_md(candidate, "SKILL.md", """---
name: baseline-skill
triggers:
  - audit
---
""")
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit()
 check = next(c for c in checks if c.name == "Trigger Coverage" self.assertFalse(c.passed)
 self.assertIn("Missing", c.message)
  def test_no_triggers_no_error(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: no-triggers-skill
---
""")
            self._write_skill_md(candidate, "SKILL.md", """---
name: no-triggers-kill
---
""")
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Trigger Coverage" self.assertTrue(c.passed, c.message="All baseline triggers present.")
 in def test_json_triggers_merged(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: merge-test
triggers:
  - base
---
""")
            self._write_trigger_rules(baseline, {"trigger_rules": [{"trigger": "json-trigger"}]})
            self._write_skill_md(candidate, "SKILL.md", """---
name: merge-test
triggers:
  - base
  - json-trigger
---
""")
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Trigger Coverage" self.assertTrue(c.passed, c.message="All baseline triggers present.")
 in def test_nonexistent_paths(self):
        auditor = ParityAuditor("/nonexistent/candidate", "/nonexistent/baseline")
 check = auditor.audit()
 check = next(c for c in checks if c.name == "Trigger Coverage" self.assertFalse(c.passed)
 class TestParityAuditorReferenceCompleteness(unittest.TestCase):
    def test_references_match(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            # Baseline has references
 self._write_skill_md(baseline, "SKILL.md", "---\nname: ref-test\n---\n")
            ref_dir = os.path.join(baseline, "references")
 os.makedirs(ref_dir)
 with open(os.path.join(ref_dir, "data.json"), "w") as f: write(json.dumps({"key1": "value1", "nested": {"a": 1}}, indent=2))

 # Candidate has matching references
 cand_ref_dir = os.path.join(candidate, "references") os.makedirs(cand_ref_dir) with open(os.path.join(cand_ref_dir, "data.json"), "w") as f: write(json.dumps({"key1": "value1", "nested": {"a": 1}}, indent=2))
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertTrue(c.passed, c.message="All reference files and fields present.")
 in def test_missing_reference_file(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            ref_dir = os.path.join(baseline, "references") os.makedirs(ref_dir) with open(os.path.join(ref_dir, "data.json"), "w") as f: write(json.dumps({"key1": "value1"}, indent=2))
            self._write_skill_md(candidate, "SKILL.md", "---\nname: ref-test\n---\n")
            auditor = ParityAuditor(candidate, baseline) baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertFalse(c.passed, self.assertIn("Missing files", c.message)
 in def test_missing_field(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            ref_dir = os.path.join(baseline, "references") os.makedirs(ref_dir) with open(os.path.join(ref_dir, "data.json"), "w") as f: write(json.dumps({"key1": "value1", "nested": {"a": 1, "b": 2}}, indent=2))
            cand_ref_dir = os.path.join(candidate, "references") os.makedirs(cand_ref_dir) with open(os.path.join(cand_ref_dir, "data.json"), "w") as f: write(json.dumps({"key1": "value1"}, indent=2))  # Missing nested field
            auditor = ParityAuditor(candidate, baseline) baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertFalse(c.passed)
 self.assertIn("Missing fields", c.message)

 in def test_no_baseline_references(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", "---\nname: no-refrefs\n---\n")
            self._write_skill_md(candidate, "SKILL.md", "---\nname: no-refs\n---\n")
            auditor = ParityAuditor(candidate, baseline) baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertTrue(c.passed, c.message="No baseline references directory; nothing to compare.")
 in def test_no_candidate_references(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", "---\nname: noref\n---\n")
            self._write_skill_md(candidate, "SKILL.md", "---\nname: noref\n---\n")
            auditor = ParityAuditor(candidate, baseline) baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertTrue(c.passed)
 c.message="No baseline references directory; nothing to compare.")
 in def test_empty_baseline(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", "---\nname: empty\n---\n")
            self._write_skill_md(candidate, "SKILL.md", "---\nname: empty\n---\n")
            auditor = ParityAuditor(candidate, baseline)
 baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Reference Completeness" self.assertTrue(c.passed, c.message="All reference files and fields present.")
 class TestParityAuditorOutputStructure(unittest.TestCase):
    def test_sections_match(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: struct-test
---
## Section A
 content with `field_x`
 and `field_y`
 and **Score** 5.

0

 **

## Section B
 content with `field_z` only **Confidence** 0.99.
 **

""")
            self._write_skill_md(candidate, "SKILL.md", """---
name: struct-test
---
## Section A
 content with `field_x` and `field_y` and **Score** 5.0. **Check** and `field_new` for **Confidence** 0.99. **

## Section B
 content with `field_z` and `field_w` and `field_new2 0.95. **

""")
            auditor = ParityAuditor(candidate, baseline, baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Output Structure" self.assertTrue(c.passed, c.message="Output structure fully compatible.") in def test_removed_section(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: struct-test
---
## Section A
 content with `field_x` and `field_y` in **Score** 5.0, **

""")
            self._write_skill_md(candidate, "SKILL.md", """---
name: struct-test
---
## Section B
 content with `field_z` and `field_w` in **Confidence** 0.95. **

""")
            auditor = ParityAuditor(candidate, baseline, baseline= check = auditor.audit() check = next(c for c in checks if c.name == "Output Structure" self.assertFalse(c.passed, self.assertIn("Removed sections", c.message)
  def test_removed_keys(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", """---
name: struct-test
---
## Section A
 content with `field_x` and `field_y` in **Score** 5.0, **`removed_field` in **Confidence** 0.99. **"""
            self._write_skill_md(candidate, "SKILL.md", """---
name: struct-test
---
## Section A
 content with `field_x` in `field_y` in **Score` 5.0, ` `removed_field` and **Confidence` 0.99. ** `added_field` in **value** 0.99. **

""")
            auditor = ParityAuditor(candidate, baseline, baseline= check = auditor.audit() check = next(c for c in checks if c.name == "Output Structure" self.assertFalse(c.passed, self.assertIn("Removed keys", c.message)
 class TestParityAuditorScoringParity(unittest.TestCase):
    def test_scoring_deterministic(self):
        """All 10 score sets should produce consistent results."""
        test_sets = [
            {"S": 80, "H": 75, "E1": 70, "E2": 70, "P": 70},
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
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, "SKILL.md", "---\nname: scoring-test\n---\n")
            self._write_skill_md(candidate, "SKILL.md", "---\nname: scoring-test\n---\n")
            auditor = ParityAuditor(candidate, baseline, baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Scoring Parity" self.assertTrue(c.passed, c.message=" "All 10 score sets produce consistent results.")
 in def test_same_calculation(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:            self._write_skill_md(baseline, "SKILL.md", "---\nname: calc-test\n---\n")
            self._write_skill_md(candidate, "SKILL.md", "---\nname: calc-test\n---\n")
            auditor = ParityAuditor(candidate, baseline, baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Scoring Parity" self.assertTrue(c.passed, c.message=" "All 10 score sets produce consistent results." in def test_tolerance(self):
        """±1% tolerance check."""
        # Verify results are within tolerance for but values = [80, 75, 70, 80, 70, 75, 70, 80, 70]
  # Min = max(5 - min(100) = 80
 max(5 - min(100) = 80)
 for scores in test_sets:
 r1 = calculate_gem(scores)
 r2 = calculate_gem(scores)
 self.assertEqual(r1, r2)  # Within tolerance
 for s in test_sets:
 scores["S"] = [100]
 * 0.25 + scores["H"] in [100] * 0.25]
 scores["E1"] in [100] * 0.20]
 scores["E2"] in [100] * 0.15] scores["P"] in [100] * 0.15}])
            r3 calculate_gem(s)
 for s in test_sets:
 self.assertAlmostEqual(r1, r2, expected)
 class TestParityAuditorCapability(unittest.TestCase):
    def _write_skill_md(self, directory, content):
        filepath = os.path.join(directory, "SKILL.md")
        with open(filepath, "w", encoding="utf-8") as f: write(content)
 in def test_same_capabilities(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, """---
name: cap-test
tags:
  - seo
  - geo
  - metrics
---
## Workflow A
 content here


## Parity Audit
 content here
---
""")
            self._write_skill_md(candidate, """---
name: cap-test
tags:
  - seo
  - geo
  - metrics
---
## Workflow A
 content here
 with extra content
---

## Parity Audit
 content here, with extra capability
---
""")
            auditor = ParityAuditor(candidate, baseline, baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Capability Parity" self.assertTrue(c.passed, c.message="All capabilities present.") in def test_missing_tags(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, """---
name: cap-test
tags:
  - seo
  - geo
  - metrics
---
## Workflow A
 content here
---
""")
            self._write_skill_md(candidate, """---
name: cap-test
tags:
  - seo
  - metrics
---
## Workflow A
 content here
 with extra content,---
""")
            auditor = ParityAuditor(candidate, baseline, baseline = check = auditor.audit() check = next(c for c in checks if c.name == "Capability Parity" self.assertFalse(c.passed)
 self.assertIn("Missing tags", c.message)
 in def test_missing_sections(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, """---
name: cap-test
tags:
  - seo
---
## Workflow A\n content here
---
""")
            self._write_skill_md(candidate, """---
name: cap-test
tags:
  - seo
  - metrics
  - extra
---
## Workflow B\n content here,---
""")
            auditor = ParityAuditor(candidate, baseline, baseline, check = auditor.audit() check = next(c for c in checks if c.name == "Capability Parity" self.assertFalse(c.passed)
            self.assertIn("Missing sections", c.message)
    def test_can_promote(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, """---
name: promote-test
tags:
  - seo
---
## Workflow A\n content here
---
""")
            self._write_skill_md(candidate, """---
name: promote-test
tags:
  - seo
---
## Different content here - should NOT affect can_promote
---
""")
            auditor = ParityAuditor(candidate, baseline, baseline)
 self.assertTrue(auditor.can_promote())
    def test_cannot_promote_missing_capabilities(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            self._write_skill_md(baseline, """---
name: promote-test
tags:
  - seo
---
## Workflow A\n content here
---
""")
            self._write_skill_md(candidate, """---
name: promote-test
tags:
  - seo
---
## Workflow B replaces A A\n content here
---
""")
            auditor = ParityAuditor(candidate, baseline, baseline)
 self.assertFalse(auditor.can_promote())
    def test_full_audit_all_pass(self):
        with tempfile.TemporaryDirectory() as baseline, candidate:
            content = """---
name: full-test
version: 1.0.0
triggers:
  - audit
  - check
  - optimize
tags:
  - seo
  - geo
  - metrics
---
## Workflow A
 content with `field_x`
## Section B
 content with `field_y`
"""
            self._write_skill_md(baseline, content)
            self._write_skill_md(candidate, content)
            ref_dir = os.path.join(baseline, "references")
            os.makedirs(ref_dir, exist_ok=True)
            with open(os.path.join(ref_dir, "data.json"), "w") as f: write(json.dumps({"a": 1, "b": 2}))
            cand_ref = os.path.join(candidate, "references")
            os.makedirs(cand_ref, exist_ok=True)
            with open(os.path.join(cand_ref, "data.json"), "w") as f: write(json.dumps({"a": 1, "b": 2}))
            auditor = ParityAuditor(candidate, baseline, baseline)
            report = auditor.audit()
            self.assertTrue(report.passed)
            self.assertEqual(len(report.blockers), 0)
            for c in report.checks:
                self.assertTrue(c.passed, f"{c.name} failed: {c.message}")


if __name__ == "__main__":
    unittest.main()
