# SeekR — Autonomous SEO + GEO Agent for Independent Sites

> AI-native search optimization agent that audits, generates content, and self-evolves.

## What is SeekR?

SeekR is an autonomous SEO and Generative Engine Optimization (GEO) agent designed for English independent sites. It continuously monitors your site's AI visibility, generates GEO-optimized articles, tracks rankings, and **self-evolves** based on performance data — without any manual intervention.

## Core Features

- **Full SEO + GEO Audit** — One command returns a complete health score (SHEEP/GEM framework), prioritized action plan, and AI citability assessment
- **Auto GEO Article Generation** — After every audit, automatically generates publish-ready GEO-optimized articles from high-opportunity keywords
- **Self-Evolution Engine** — Monitors SHEEP scores over time, detects degradation, generates optimization strategies, validates via A/B testing, and promotes winners automatically
- **Zero Confirmation Workflow** — Never asks "should I continue?" — executes the full pipeline from URL to published content

## Prerequisites

- **Python 3.8+**
- **Claude Code >= 1.0**
- At least one LLM API Key (Gemini / Claude / OpenAI-compatible)
- 30+ SEO/GEO sub-skills (managed automatically by `install.py`)

## Quick Start

1. **Install dependencies**
   ```bash
   python install.py init        # Interactive API key configuration
   python install.py --install   # Check and install required skills
   python install.py validate    # Verify installation integrity
   ```

2. **Run audit**
   ```
   /seekr audit my site https://yoursite.com
   ```

## Architecture

```
User Request → /seekr
                    |
         +-----------------------------+
         |  Workflow A: Full SEO+GEO Audit      |
         |  Workflow B: Keyword Optimization    |
         |  Workflow C: GEO Visibility Plan     |
         |  Workflow D: GEO Article Generation  |
         +--------------+----------------+
                        |
         geo_optimizer.py (SHEEP Scoring)
                        |
         seekr-evolve/evolution-metrics/<id>.json
                        |
         /seekr-evolve
         +-----------------------------+
         |  Metrics Collector > Pattern Recognizer |
         |  > Strategy Generator > A/B Testing     |
         |  > Snapshot Versioning > Parity Audit   |
         +-----------------------------+
```

For detailed skill design, see [seekr/SKILL.md](seekr/SKILL.md) and [seekr-evolve/SKILL.md](seekr-evolve/SKILL.md).

## SHEEP Framework

SeekR uses the **SHEEP framework** for GEO scoring:

| Dimension | Weight | Description |
|---|---|---|
| **S** — Semantic Coverage | 25% | Keyword depth, topic authority |
| **H** — Human Credibility | 25% | E-E-A-T, author credentials, citations |
| **E1** — Evidence Structuring | 20% | Schema markup, FAQ, data tables |
| **E2** — Ecosystem Integration | 15% | Brand mentions, external links, social |
| **P** — Performance Monitoring | 15% | Content freshness, technical speed |

**GEM Score** = Weighted sum across all 5 dimensions (0-100)

## Skills Ecosystem

SeekR integrates 30+ SEO/GEO skills including:

- `seo-technical`, `seo-content`, `seo-schema`, `seo-audit`
- `geo-audit`, `geo-citability`, `geo-crawlers`, `geo-llmstxt`
- `keyword-research`, `serp-analysis`, `backlink-analyzer`
- `seo-content-writer`, `geo-content-optimizer`, `schema-markup-generator`

## Tech Stack

- **Skills**: Claude Code native Skills format (Markdown)
- **Evolution**: Python + JSON snapshots + A/B testing
- **Scoring**: SHEEP/GEM framework (geo_optimizer.py)
- **Content**: Markdown output with inline JSON-LD (CMS-ready)

## Troubleshooting

| Problem | Solution |
|---|---|
| "Missing skill xxx" | Run `python install.py --install` or `claude /find-skills xxx` |
| "API key for 'xxx' is empty" | Run `python install.py init` to reconfigure |
| "config.yaml not found" | Copy from `config.yaml.example` or run `python install.py init` |

## License

CC BY-NC-SA 4.0
