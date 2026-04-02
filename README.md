# SeekR — Autonomous SEO + GEO Agent for Independent Sites

> AI-native search optimization agent that audits, generates content, and self-evolves.

## What is SeekR?

SeekR is an autonomous SEO and Generative Engine Optimization (GEO) agent designed for English independent sites. It continuously monitors your site's AI visibility, generates GEO-optimized articles, tracks rankings, and **self-evolves** based on performance data — without any manual intervention.

## Core Features

- **Full SEO + GEO Audit** — One command returns a complete health score (SHEEP/GEM framework), prioritized action plan, and AI citability assessment
- **Auto GEO Article Generation** — After every audit, automatically generates publish-ready GEO-optimized articles from high-opportunity keywords
- **Self-Evolution Engine** — Monitors SHEEP scores over time, detects degradation, generates optimization strategies, validates via A/B testing, and promotes winners automatically
- **Zero Confirmation Workflow** — Never asks "should I continue?" — executes the full pipeline from URL to published content

## Quick Start

```bash
# Full site audit + auto article generation
/seo-geo-master-orchestrator audit my site https://yoursite.com

# GEO article generation
/seo-geo-master-orchestrator write GEO article "best AI tools 2026"

# Trigger self-evolution cycle
/seo-geo-evolution-engine evolve
```

## Architecture

```
User Request → seo-geo-master-orchestrator
                    ↓
         ┌──────────────────────────────────────┐
         │  Workflow A: Full SEO+GEO Audit      │
         │  Workflow B: Keyword Optimization    │
         │  Workflow C: GEO Visibility Plan     │
         │  Workflow D: GEO Article Generation  │
         └──────────────┬───────────────────────┘
                        ↓
         geo_optimizer.py (SHEEP Scoring)
                        ↓
         geoclaw/evolution-metrics/<id>.json
                        ↓
         seo-geo-evolution-engine
         ┌──────────────────────────────────────┐
         │  Metrics Collector → Pattern Recognizer│
         │  → Strategy Generator → A/B Testing   │
         │  → Snapshot Versioning → Parity Audit │
         └──────────────────────────────────────┘
```

## SHEEP Framework

SeekR uses the **SHEEP framework** for GEO scoring:

| Dimension | Weight | Description |
|---|---|---|
| **S** — Semantic Coverage | 25% | Keyword depth, topic authority |
| **H** — Human Credibility | 25% | E-E-A-T, author credentials, citations |
| **E1** — Evidence Structuring | 20% | Schema markup, FAQ, data tables |
| **E2** — Ecosystem Integration | 15% | Brand mentions, external links, social |
| **P** — Performance Monitoring | 15% | Content freshness, technical speed |

**GEM Score** = Weighted sum across all 5 dimensions (0–100)

## Skills Ecosystem

SeekR integrates 50+ SEO/GEO skills including:

- `seo-technical`, `seo-content`, `seo-schema`, `seo-audit`
- `geo-audit`, `geo-citability`, `geo-crawlers`, `geo-llmstxt`
- `keyword-research`, `serp-analysis`, `backlink-analyzer`
- `seo-content-writer`, `geo-content-optimizer`, `schema-markup-generator`

## Tech Stack

- **Skills**: Claude Code native Skills format (Markdown)
- **Evolution**: Python + JSON snapshots + A/B testing
- **Scoring**: SHEEP/GEM framework (geo_optimizer.py)
- **Content**: Markdown output with inline JSON-LD (CMS-ready)

## License

CC BY-NC-SA 4.0
