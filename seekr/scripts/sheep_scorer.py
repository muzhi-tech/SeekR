"""SHEEP Scoring Engine for SeekR Openclaw.

Scores content across five dimensions (Semantic, Human-credibility,
Evidence Structuring, Ecosystem Integration, Performance Monitoring),
computes a weighted GEM score, applies platform-specific adjustments,
and writes execution metrics.

Pure Python stdlib. Imports from seekr.scripts.models.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from seekr.scripts.models import (
    CRITICAL_THRESHOLD,
    DIMENSIONS,
    DIMENSION_WEIGHTS,
    WARNING_THRESHOLD,
    calculate_gem,
    gem_band,
    new_execution_id,
    now_iso,
    sheep_status,
)

# Path to platforms.json (relative to this file)
_PLATFORMS_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, "references", "platforms.json"
)

# Platform boost multiplier for priority dimensions
_PRIORITY_BOOST = 1.15


class SheepScorer:
    """Score content against the SHEEP framework."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.platforms: Dict[str, Any] = self._load_platforms()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_platforms() -> Dict[str, Any]:
        path = os.path.normpath(_PLATFORMS_PATH)
        if not os.path.isfile(path):
            return {}
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("platforms", {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_content(self, content: Dict) -> Dict:
        """Main entry point. Returns full SHEEP scoring result."""
        s = self._score_semantic(content)
        h = self._score_human_credibility(content)
        e1 = self._score_evidence_structuring(content)
        e2 = self._score_ecosystem_integration(content)
        p = self._score_performance_monitoring(content)

        sheep_scores = {"S": s["total"], "H": h["total"], "E1": e1["total"], "E2": e2["total"], "P": p["total"]}
        gem = calculate_gem(sheep_scores)

        result: Dict[str, Any] = {
            "sheep_scores": {k: round(v, 1) for k, v in sheep_scores.items()},
            "gem_score": gem,
            "gem_band": gem_band(gem),
            "dimension_details": {
                "S": s["breakdown"],
                "H": h["breakdown"],
                "E1": e1["breakdown"],
                "E2": e2["breakdown"],
                "P": p["breakdown"],
            },
            "platform_adjusted": self._platform_adjustments(sheep_scores),
        }
        return result

    # ------------------------------------------------------------------
    # Dimension: S - Semantic Coverage  (0-100)
    # ------------------------------------------------------------------

    def _score_semantic(self, content: Dict) -> Dict:
        text = content.get("text", "")
        keywords = content.get("keywords", [])
        headings = content.get("headings", [])

        keyword_pts = self._clamp(len(set(keywords)) * 2, 0, 30)
        content_depth = self._content_depth_points(text)
        topic_breadth = self._clamp(len(headings) * 2, 0, 20)
        semantic_density = self._semantic_density_points(text, keywords)

        total = self._clamp(keyword_pts + content_depth + topic_breadth + semantic_density, 0, 100)
        return {
            "total": total,
            "breakdown": {
                "keyword_count": keyword_pts,
                "content_depth": content_depth,
                "topic_breadth": topic_breadth,
                "semantic_density": semantic_density,
            },
        }

    @staticmethod
    def _content_depth_points(text: str) -> int:
        wc = len(text.split())
        if wc < 500:
            return 0
        if wc < 1000:
            return 15
        if wc < 2000:
            return 25
        return 30

    @staticmethod
    def _semantic_density_points(text: str, keywords: List[str]) -> int:
        if not text or not keywords:
            return 0
        text_lower = text.lower()
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        ratio = found / len(keywords)
        return int(min(ratio * 20, 20))

    # ------------------------------------------------------------------
    # Dimension: H - Human Credibility  (0-100)
    # ------------------------------------------------------------------

    def _score_human_credibility(self, content: Dict) -> Dict:
        author_pts = self._author_points(content)
        citation_pts = self._citation_points(content)
        eeat_pts = self._eeat_points(content)
        stats_pts = self._statistics_points(content)

        total = self._clamp(author_pts + citation_pts + eeat_pts + stats_pts, 0, 100)
        return {
            "total": total,
            "breakdown": {
                "author_credentials": author_pts,
                "citations_count": citation_pts,
                "eeat_signals": eeat_pts,
                "statistics_present": stats_pts,
            },
        }

    @staticmethod
    def _author_points(content: Dict) -> int:
        pts = 0
        author = content.get("author", "")
        bio = content.get("author_bio", "")
        credentials = content.get("author_credentials", "")
        if author:
            pts += 8
        if bio:
            pts += 8
        if credentials:
            pts += 9
        return min(pts, 25)

    @staticmethod
    def _citation_points(content: Dict) -> int:
        citations = content.get("citations", [])
        count = len(citations)
        if count == 0:
            return 0
        if count <= 3:
            return 10
        if count <= 6:
            return 20
        return 25

    @staticmethod
    def _eeat_points(content: Dict) -> int:
        pts = 0
        text = content.get("text", "").lower()
        eeat_keywords = [
            "expert", "research", "study", "phd", "professor",
            "experience", "certified", "published", "peer-reviewed",
        ]
        for kw in eeat_keywords:
            if kw in text:
                pts += 3
        # Check for structured EEAT markers
        if content.get("author_credentials"):
            pts += 4
        if content.get("author_bio"):
            pts += 4
        return min(pts, 25)

    @staticmethod
    def _statistics_points(content: Dict) -> int:
        text = content.get("text", "")
        if not text:
            return 0
        # Count numbers, percentages, and data patterns
        percent_matches = re.findall(r"\d+\.?\d*\s*%", text)
        number_matches = re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", text)
        stat_indicators = len(percent_matches) + len(number_matches)
        words = len(text.split())
        if words == 0:
            return 0
        ratio = stat_indicators / (words / 200)  # normalize per 200 words
        return int(min(ratio * 8, 25))

    # ------------------------------------------------------------------
    # Dimension: E1 - Evidence Structuring  (0-100)
    # ------------------------------------------------------------------

    def _score_evidence_structuring(self, content: Dict) -> Dict:
        schema_pts = self._schema_points(content)
        faq_pts = self._faq_points(content)
        table_pts = self._table_points(content)
        heading_pts = self._heading_structure_points(content)

        total = self._clamp(schema_pts + faq_pts + table_pts + heading_pts, 0, 100)
        return {
            "total": total,
            "breakdown": {
                "schema_markup": schema_pts,
                "faq_present": faq_pts,
                "data_tables": table_pts,
                "heading_structure": heading_pts,
            },
        }

    @staticmethod
    def _schema_points(content: Dict) -> int:
        schema = content.get("schema", "")
        if not schema:
            return 0
        # Check if valid JSON-LD-like structure
        if isinstance(schema, dict):
            return 25 if schema.get("@type") or schema.get("@context") else 10
        if isinstance(schema, str):
            try:
                parsed = json.loads(schema)
                if isinstance(parsed, dict) and (parsed.get("@type") or parsed.get("@context")):
                    return 25
                return 10
            except (json.JSONDecodeError, ValueError):
                return 5
        return 5

    @staticmethod
    def _faq_points(content: Dict) -> int:
        faq = content.get("faq", [])
        text = content.get("text", "")
        if faq and len(faq) > 0:
            return 25
        # Check for FAQ patterns in text
        if re.search(r"(?i)(frequently asked|FAQ|common questions)", text):
            return 15
        return 0

    @staticmethod
    def _table_points(content: Dict) -> int:
        tables = content.get("tables", [])
        text = content.get("text", "")
        if tables and len(tables) > 0:
            return min(len(tables) * 10, 25)
        # Check for table-like patterns in HTML/markdown
        table_patterns = re.findall(r"<table|(\|.+\|.+\|)", text)
        return min(len(table_patterns) * 8, 25)

    @staticmethod
    def _heading_structure_points(content: Dict) -> int:
        headings = content.get("headings", [])
        if not headings:
            return 0
        pts = 0
        # Check for H1 presence
        has_h1 = any(h.get("level") == 1 or re.match(r"^#\s", str(h)) for h in headings)
        if has_h1:
            pts += 8
        # Check hierarchy: H1 -> H2 -> H3
        levels = []
        for h in headings:
            if isinstance(h, dict):
                levels.append(h.get("level", 0))
            elif isinstance(h, str):
                match = re.match(r"^(#{1,6})\s", h)
                levels.append(len(match.group(1)) if match else 0)
        if levels:
            # Reward proper nesting (no skipping levels)
            proper = all(levels[i] <= levels[i + 1] + 1 for i in range(len(levels) - 1))
            pts += 10 if proper else 4
        # Bonus for multiple heading levels
        unique_levels = set(levels) - {0}
        pts += min(len(unique_levels) * 3, 7)
        return min(pts, 25)

    # ------------------------------------------------------------------
    # Dimension: E2 - Ecosystem Integration  (0-100)
    # ------------------------------------------------------------------

    def _score_ecosystem_integration(self, content: Dict) -> Dict:
        link_pts = self._external_link_points(content)
        social_pts = self._social_signal_points(content)
        brand_pts = self._brand_consistency_points(content)
        nap_pts = self._nap_consistency_points(content)

        total = self._clamp(link_pts + social_pts + brand_pts + nap_pts, 0, 100)
        return {
            "total": total,
            "breakdown": {
                "external_links": link_pts,
                "social_signals": social_pts,
                "brand_consistency": brand_pts,
                "nap_consistency": nap_pts,
            },
        }

    @staticmethod
    def _external_link_points(content: Dict) -> int:
        links = content.get("links", [])
        if not links:
            return 0
        # Differentiate quality (domain diversity)
        domains = set()
        for link in links:
            if isinstance(link, str):
                match = re.search(r"https?://([^/]+)", link)
                if match:
                    domains.add(match.group(1))
            elif isinstance(link, dict):
                url = link.get("url", "")
                match = re.search(r"https?://([^/]+)", url)
                if match:
                    domains.add(match.group(1))
        if len(domains) >= 5:
            return 25
        if len(domains) >= 3:
            return 18
        if len(domains) >= 1:
            return 10
        return 0

    @staticmethod
    def _social_signal_points(content: Dict) -> int:
        pts = 0
        if content.get("social_share_buttons"):
            pts += 8
        if content.get("og_tags"):
            pts += 8
        if content.get("twitter_cards"):
            pts += 5
        text = content.get("text", "").lower()
        if re.search(r"(twitter|facebook|linkedin|instagram|youtube|reddit)", text):
            pts += 4
        return min(pts, 25)

    @staticmethod
    def _brand_consistency_points(content: Dict) -> int:
        pts = 0
        brand = content.get("brand_name", "")
        logo = content.get("brand_logo", "")
        consistent_tone = content.get("brand_tone_consistent", False)
        if brand:
            pts += 8
        if logo:
            pts += 8
        if consistent_tone:
            pts += 9
        return min(pts, 25)

    @staticmethod
    def _nap_consistency_points(content: Dict) -> int:
        pts = 0
        name = content.get("business_name", "")
        address = content.get("business_address", "")
        phone = content.get("business_phone", "")
        if name:
            pts += 8
        if address:
            pts += 8
        if phone:
            pts += 9
        return min(pts, 25)

    # ------------------------------------------------------------------
    # Dimension: P - Performance Monitoring  (0-100)
    # ------------------------------------------------------------------

    def _score_performance_monitoring(self, content: Dict) -> Dict:
        freshness_pts = self._freshness_points(content)
        update_pts = self._update_frequency_points(content)
        tech_pts = self._technical_score_points(content)
        mobile_pts = self._mobile_friendly_points(content)

        total = self._clamp(freshness_pts + update_pts + tech_pts + mobile_pts, 0, 100)
        return {
            "total": total,
            "breakdown": {
                "content_freshness": freshness_pts,
                "update_frequency": update_pts,
                "technical_score": tech_pts,
                "mobile_friendly": mobile_pts,
            },
        }

    @staticmethod
    def _freshness_points(content: Dict) -> int:
        updated = content.get("last_updated", "")
        if not updated:
            return 5  # minimal credit if unknown
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days = (now - dt).days
            if days <= 30:
                return 25
            if days <= 90:
                return 18
            if days <= 180:
                return 10
            return 5
        except (ValueError, TypeError):
            return 5

    @staticmethod
    def _update_frequency_points(content: Dict) -> int:
        history = content.get("update_history", [])
        if not history:
            return 0
        # More updates = better
        count = len(history)
        if count >= 5:
            return 25
        if count >= 3:
            return 18
        if count >= 1:
            return 10
        return 0

    @staticmethod
    def _technical_score_points(content: Dict) -> int:
        tech = content.get("technical_metrics", {})
        if not tech:
            return 0
        load_speed = tech.get("load_speed_ms", 0)
        pts = 0
        if load_speed > 0:
            if load_speed < 1500:
                pts += 12
            elif load_speed < 3000:
                pts += 7
            else:
                pts += 3
        core_vitals = tech.get("core_web_vitals_pass", False)
        if core_vitals:
            pts += 8
        https = tech.get("https_enabled", False)
        if https:
            pts += 5
        return min(pts, 25)

    @staticmethod
    def _mobile_friendly_points(content: Dict) -> int:
        pts = 0
        if content.get("responsive_design", False):
            pts += 10
        if content.get("viewport_meta", False):
            pts += 7
        if content.get("mobile_usability_pass", False):
            pts += 8
        return min(pts, 25)

    # ------------------------------------------------------------------
    # Platform adjustments
    # ------------------------------------------------------------------

    def _platform_adjustments(self, sheep_scores: Dict[str, float]) -> Dict[str, Any]:
        """Apply platform-specific priority dimension boosts."""
        adjusted: Dict[str, Any] = {}
        for pid, pdata in self.platforms.items():
            priority_dims: List[str] = pdata.get("sheep_priority", [])
            # Apply boost to priority dimensions
            boosted = dict(sheep_scores)
            for dim in priority_dims:
                if dim in boosted:
                    boosted[dim] = min(round(boosted[dim] * _PRIORITY_BOOST, 1), 100.0)
            adjusted[pid] = {
                "gem": calculate_gem(boosted),
                "priority_dims": priority_dims,
            }
        return adjusted

    # ------------------------------------------------------------------
    # Execution metric writer
    # ------------------------------------------------------------------

    def write_execution_metric(self, result: Dict, output_dir: str) -> str:
        """Write scoring result to evolution-metrics/ as a JSON file.

        Returns the path of the written file.
        """
        metrics_dir = os.path.join(output_dir, "evolution-metrics")
        os.makedirs(metrics_dir, exist_ok=True)

        timestamp = now_iso()
        filename = f"sheep_{new_execution_id()}.json"
        filepath = os.path.join(metrics_dir, filename)

        metric = {
            "execution_id": new_execution_id(),
            "timestamp": timestamp,
            "sheep_scores": result.get("sheep_scores", {}),
            "gem_score": result.get("gem_score", 0),
            "gem_band": result.get("gem_band", "F"),
            "dimension_details": result.get("dimension_details", {}),
            "platform_adjusted": result.get("platform_adjusted", {}),
        }

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(metric, fh, indent=2, ensure_ascii=False)

        return filepath

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))


# ======================================================================
# CLI demo
# ======================================================================

if __name__ == "__main__":
    sample_content = {
        "text": (
            "This is a comprehensive guide to SEO optimization in 2024. "
            "According to recent studies by experts, 75% of users never scroll past the first page. "
            "Our research shows that 1,250,000 websites use structured data. "
            "The professor Dr. Jane Smith, PhD, published a peer-reviewed analysis "
            "showing that organic traffic grew by 42.3% with proper schema markup. "
            "Expert recommendations include focusing on user experience, mobile optimization, "
            "and high-quality content. Research from certified professionals indicates "
            "that technical SEO foundations are critical. This guide covers everything "
            "from keyword research to advanced link building strategies. "
            "We interviewed 50 industry experts to compile these findings. "
        ) * 20,  # ~500+ words
        "keywords": [
            "SEO", "optimization", "search engine", "ranking", "traffic",
            "keywords", "backlinks", "content", "technical SEO", "schema",
            "organic", "SERP", "crawlability", "indexing", "page speed",
        ],
        "headings": [
            {"level": 1, "text": "Ultimate SEO Guide 2024"},
            {"level": 2, "text": "What is SEO?"},
            {"level": 2, "text": "Key Ranking Factors"},
            {"level": 3, "text": "Content Quality"},
            {"level": 3, "text": "Technical SEO"},
            {"level": 2, "text": "Advanced Strategies"},
            {"level": 3, "text": "Schema Markup"},
            {"level": 3, "text": "Link Building"},
        ],
        "author": "Dr. Jane Smith",
        "author_bio": "SEO researcher with 15 years of experience in digital marketing.",
        "author_credentials": "PhD in Computer Science, Google Certified Professional",
        "citations": [
            "https://example.com/study1",
            "https://example.com/study2",
            "https://example.com/study3",
            "https://example.com/study4",
        ],
        "schema": {"@type": "Article", "@context": "https://schema.org"},
        "faq": [
            {"q": "What is SEO?", "a": "SEO is the practice of optimizing websites."},
            {"q": "How long does SEO take?", "a": "Typically 3-6 months for results."},
        ],
        "tables": [{"headers": ["Factor", "Weight"], "rows": [["Content", "40%"]]}],
        "links": [
            "https://developers.google.com/search",
            "https://moz.com/beginners-guide-to-seo",
            "https://searchengineland.com/guide/seo",
            "https://ahrefs.com/blog/seo-basics",
        ],
        "social_share_buttons": True,
        "og_tags": True,
        "twitter_cards": True,
        "brand_name": "SEO Mastery",
        "brand_logo": "https://example.com/logo.png",
        "brand_tone_consistent": True,
        "business_name": "SEO Mastery Inc.",
        "business_address": "123 Digital Ave, San Francisco, CA",
        "business_phone": "+1-555-123-4567",
        "last_updated": "2025-12-01T10:00:00Z",
        "update_history": ["2025-12-01", "2025-09-15", "2025-06-01", "2025-03-01", "2024-12-01"],
        "technical_metrics": {
            "load_speed_ms": 1200,
            "core_web_vitals_pass": True,
            "https_enabled": True,
        },
        "responsive_design": True,
        "viewport_meta": True,
        "mobile_usability_pass": True,
    }

    scorer = SheepScorer()
    result = scorer.score_content(sample_content)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Optionally write metric
    output_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    path = scorer.write_execution_metric(result, output_dir)
    print(f"\nMetric written to: {path}")
