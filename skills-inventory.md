# SEO/GEO Skills Inventory & Workflow Map

**Date:** 2026-04-03
**Purpose:** Complete analysis of all installed SEO/GEO skills, their boundaries, I/O formats, triggers, and workflow integration patterns.

---

## 1. Skills Classification Map

### 1.1 GEO-Primary Skills (Agent-Based)

These skills are **composite/orchestrator** skills that delegate to sub-skills. They serve as the entry points for GEO-specific workflows.

| Skill | Type | File Location | Responsibility | Input | Output | Triggers | Dependencies |
|-------|------|---------------|----------------|-------|--------|----------|--------------|
| `geo` | Orchestrator | `~/.claude/skills/geo/SKILL.md` | GEO-first SEO analysis. Full audits, citability scoring, AI crawler analysis, llms.txt generation, brand mention scanning, platform-specific optimization, schema markup, technical SEO, content E-E-A-T, PDF report generation | URL | `GEO-AUDIT-REPORT.md`, `GEO-REPORT.pdf` | "geo", "seo", "audit", "AI search", "AI visibility", "optimize", "citability", "llms.txt", "schema", "brand mentions", "GEO report" | geo-audit, geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions, geo-platform-optimizer, geo-schema, geo-technical, geo-content, geo-report, geo-report-pdf |
| `geo-audit` | Orchestrator | `~/.claude/skills/geo-audit/SKILL.md` | Full website GEO+SEO audit with parallel subagent delegation. Produces composite GEO Score (0-100) | URL | GEO Audit Report with scores | "geo audit", "full geo analysis" | Subagents: geo-ai-visibility, geo-platform-analysis, geo-technical, geo-content, geo-schema |
| `geo-ai-visibility` | Agent | `~/.claude/agents/geo-ai-visibility.md` | Citability scoring, AI crawler access, llms.txt compliance, brand mention presence across AI-cited platforms | URL | AI Visibility Score section (markdown) | Embedded in geo-audit | Delegates: geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions |
| `geo-platform-analysis` | Agent | `~/.claude/agents/geo-platform-analysis.md` | Platform-specific optimization for Google AI Overviews, ChatGPT, Perplexity, Gemini, Bing Copilot | URL | Platform Readiness Score per platform | Embedded in geo-audit | None |
| `geo-technical` | Agent | `~/.claude/agents/geo-technical.md` | Technical SEO with GEO-specific checks: crawlability, SSR, Core Web Vitals (INP), AI crawler access | URL | Technical Score section | Embedded in geo-audit | None |
| `geo-content` | Agent | `~/.claude/agents/geo-content.md` | Content quality E-E-A-T assessment for AI citability | URL | Content Score section | Embedded in geo-audit | None |
| `geo-schema` | Agent | `~/.claude/agents/geo-schema.md` | Schema.org structured data audit and generation optimized for AI discoverability | URL | Schema Score section + JSON-LD templates | Embedded in geo-audit | None |
| `geo-report` | Skill | `~/.claude/skills/geo-report/SKILL.md` | Generate client-facing GEO report combining all audit results | Audit data | Client-ready GEO report (markdown) | "geo report", "generate report" | Requires prior geo-audit |
| `geo-report-pdf` | Skill | `~/.claude/skills/geo-report-pdf/SKILL.md` | Generate professional PDF report from GEO audit data using ReportLab | Audit JSON data | `GEO-REPORT.pdf` | "geo pdf report", "export PDF" | Requires prior geo-audit |

### 1.2 GEO Sub-Skills (Atomic)

These are **atomic skills** that perform single, focused GEO operations. They are called by orchestrators or directly by users.

| Skill | Type | Responsibility | Input | Output | Triggers |
|-------|------|---------------|-------|--------|----------|
| `geo-citability` | Atomic | AI citability scoring and optimization. Analyzes passage-level citation readiness (0-100) | URL | Citability Score, rewrite suggestions | "citability", "AI citation", "passage scoring" |
| `geo-crawlers` | Atomic | AI crawler access analysis. Checks robots.txt, meta tags, HTTP headers for AI bot access | URL | Crawler Access Score, AI bot allow/block map | "AI crawlers", "robots.txt analysis", "bot access" |
| `geo-llmstxt` | Atomic | Analyzes and generates llms.txt files. Validates existing or generates from scratch | URL | llms.txt status score + file content | "llms.txt", "AI sitemap", "RSL licensing" |
| `geo-brand-mentions` | Atomic | Brand mention and authority scanner for AI visibility. Wikipedia, Reddit, YouTube, LinkedIn presence | Brand name | Brand Authority Score (0-100) | "brand mentions", "brand authority", "Wikipedia presence" |
| `geo-platform-optimizer` | Atomic | Platform-specific AI search optimization for individual platforms | URL + platform | Platform-specific recommendations | "platform optimization", "ChatGPT optimization", "Perplexity optimization" |

### 1.3 SEO Skills (Agent/Skill-Based)

| Skill | Type | File Location | Responsibility | Input | Output | Triggers | Dependencies |
|-------|------|---------------|----------------|-------|--------|----------|--------------|
| `seo` | Orchestrator | `~/.claude/skills/seo/SKILL.md` | Universal SEO analysis. Full site audits, single-page analysis, technical SEO, schema, content, images, sitemap, GEO, local, maps, Google APIs | URL + command | Unified SEO Health Score (0-100), prioritized action plan | "SEO", "audit", "schema", "Core Web Vitals", "sitemap", "E-E-A-T", "AI Overviews", "GEO", "technical SEO", "content quality" | Delegates to 12 subagents in parallel |
| `seo-technical` | Subagent | `~/.claude/skills/seo/agents/seo-technical.md` | Technical SEO: crawlability, indexability, security, URL structure, mobile, Core Web Vitals (INP), JS rendering | URL | Technical SEO Score (0-100), categorized findings | Embedded in seo audit | None |
| `seo-content` | Subagent | `~/.claude/skills/seo/agents/seo-content.md` | E-E-A-T content quality assessment, readability, AI citation readiness, thin content detection | URL | Content Quality Score (0-100), E-E-A-T breakdown | Embedded in seo audit | None |
| `seo-schema` | Subagent | `~/.claude/skills/seo/agents/seo-schema.md` | Schema markup detection, validation, generation (JSON-LD preferred) | URL | Schema Score (0-100), detected schemas, generated templates | Embedded in seo audit | None |
| `seo-sitemap` | Subagent | `~/.claude/skills/seo/agents/seo-sitemap.md` | XML sitemap validation and generation, quality gates for location pages | URL or "generate" | Validation report, generated sitemap XML | Embedded in seo audit | None |
| `seo-visual` | Subagent | `~/.claude/skills/seo/agents/seo-visual.md` | Screenshots via Playwright, mobile responsiveness testing, above-the-fold analysis | URL | Screenshots + visual analysis | Embedded in seo audit (optional) | Requires playwright |
| `seo-performance` | Subagent | `~/.claude/skills/seo/agents/seo-performance.md` | Core Web Vitals measurement (LCP, INP, CLS) via PSI/CrUX | URL | Performance Score, CWV status per metric | Embedded in seo audit | Requires google_auth credentials |
| `seo-geo` | Subagent | `~/.claude/skills/seo/agents/seo-geo.md` | AI Overviews/GEO optimization: crawler access, llms.txt, citability, brand mentions, platform readiness | URL | GEO Readiness Score (0-100) | Embedded in seo audit | Optional DataForSEO MCP |
| `seo-local` | Subagent | `~/.claude/skills/seo/agents/seo-local.md` | Local SEO: GBP signals, NAP consistency, citations, reviews, local schema, multi-location | URL | Local SEO Score (0-100), GBP checklist | Embedded if local business detected | None |
| `seo-maps` | Subagent | `~/.claude/skills/seo/agents/seo-maps.md` | Maps intelligence: geo-grid rank tracking, GBP auditing, review intelligence, competitor radius | Business name/location | Maps Health Score (0-100) | Embedded if local + DataForSEO available | DataForSEO MCP (Tier 1) or free APIs (Tier 0) |
| `seo-google` | Subagent | `~/.claude/skills/seo/agents/seo-google.md` | Google SEO API data: CrUX field data, GSC, URL inspection, GA4 organic traffic | URL | Google API data tables, CWV ratings | Embedded if Google API credentials detected | google_auth credentials |
| `seo-dataforseo` | Subagent | `~/.claude/skills/seo/agents/seo-dataforseo.md` | Live SERP data, keyword metrics, backlinks, on-page analysis via DataForSEO MCP | Query/API call | Live SEO data | Extension, on-demand | DataForSEO MCP |
| `seo-image-gen` | Subagent | `~/.claude/skills/seo/agents/seo-image-gen.md` | SEO image audit: OG images, alt text, formats, sizes + generation plan (no auto-generation) | URL | Image audit summary + generation plan | Embedded if nanobanana-mcp available | nanobanana-mcp |

### 1.4 Marketing Skills (SEO/GEO Extension)

These are **atomic skills** from the `marketingskills` and `aaron-he-zhu/seo-geo-claude-skills` libraries.

#### Research Layer

| Skill | Responsibility | Input | Output | Triggers | Dependencies |
|-------|---------------|-------|--------|----------|--------------|
| `keyword-research` | Keyword discovery, intent classification, difficulty scoring, topic clustering, GEO relevance | Topic/product description | Ranked keyword lists, topic clusters, content calendar | "find keywords", "keyword research", "search volume", "topic ideas", "content opportunities" | Ahrefs/SEMrush API (optional) |
| `serp-analysis` | SERP composition analysis, ranking factor identification, SERP feature mapping, AI Overview analysis | Keyword | SERP feature map, ranking patterns, content requirements, difficulty score | "analyze search results", "SERP analysis", "what ranks for", "why does this page rank", "AI overviews" | WebFetch |
| `backlink-analyzer` | Backlink profile analysis, toxic link detection, link building opportunity discovery | Domain | Profile overview, toxic links, opportunity prospects | "analyze backlinks", "check link profile", "toxic links", "link building", "off-page SEO" | Ahrefs/SEMrush API (optional) |
| `content-gap-analysis` | Keyword gap analysis, topic coverage mapping, GEO opportunity detection | Your site + competitor URLs | Gap list, topic clusters, prioritized content calendar | "find content gaps", "what am I missing", "content opportunities", "competitor gaps" | SEO tool data (optional) |
| `competitor-analysis` | Full competitor analysis: keywords, traffic, content, backlink strategies | Competitor URLs | Comprehensive competitor profiles | "competitor analysis", "who ranks for this", "competitor research" | SEO tool data (optional) |

#### Build Layer

| Skill | Responsibility | Input | Output | Triggers |
|-------|---------------|-------|--------|----------|
| `seo-content-writer` | SEO-optimized content creation based on keyword research and SERP analysis | Keyword + content brief | Full article with optimized title, headers, meta, body | "write content", "create page", "SEO content" |
| `geo-content-optimizer` | Optimize existing content for AI citability and GEO | URL + keyword | Rewritten passages with higher citability scores | "optimize for AI", "GEO content", "AI citation optimization" |
| `meta-tags-optimizer` | Optimize title tags and meta descriptions for CTR | URL + keyword | Optimized title, meta description | "meta tags", "title optimization", "CTR optimization" |
| `schema-markup-generator` | Generate JSON-LD schema markup from templates | Page type + business data | Complete JSON-LD code blocks | "generate schema", "schema markup", "structured data" |

#### Optimize Layer

| Skill | Responsibility | Input | Output | Triggers |
|-------|---------------|-------|--------|----------|
| `on-page-seo-auditor` | On-page SEO audit: title, meta, headers, content, internal links, images, URL | URL + target keyword | On-page SEO score (0-100), issue list, recommendations | "audit page SEO", "on-page check", "SEO score", "page optimization" | WebFetch |
| `technical-seo-checker` | Technical SEO audit: CWV, crawlability, indexability, mobile, security, hreflang | URL | Technical health score (0-100), critical/high/medium issues | "technical SEO audit", "Core Web Vitals", "crawl errors", "site health" | WebFetch |
| `internal-linking-optimizer` | Internal link architecture analysis and recommendations | URL or site | Link architecture map, improvement recommendations | "internal links", "link architecture", "site structure" |
| `content-refresher` | Identify and update outdated content to maintain rankings | Site inventory | Refresh priorities, updated content plan | "refresh content", "outdated content", "content update" |

#### Monitor Layer

| Skill | Responsibility | Input | Output | Triggers |
|-------|---------------|-------|--------|----------|
| `rank-tracker` | Keyword ranking monitoring and trend analysis | Keywords + domains | Ranking positions, trend charts, alerts | "track rankings", "keyword positions", "ranking changes" |
| `performance-reporter` | Track and report Core Web Vitals and speed metrics over time | URL + time range | Performance trend reports | "performance report", "speed tracking", "CWV monitoring" |
| `backlink-monitor` | Ongoing backlink tracking and change detection | Domain | New/lost links report, alerts | "monitor backlinks", "link alerts" |
| `alert-manager` | Configure and manage SEO alerts for issues | Alert rules | Alert configuration | "SEO alerts", "issue notifications" |

#### Cross-Cutting

| Skill | Responsibility | Input | Output | Triggers |
|-------|---------------|-------|--------|----------|
| `content-quality-auditor` | 80-item CORE-EEAT benchmark audit | URL | Full E-E-A-T score breakdown | "E-E-A-T audit", "content quality", "quality assessment" |
| `domain-authority-auditor` | Domain authority scoring (CITE framework: Citation, Intelligence, Trust, Engagement) | Domain | DA score with dimension breakdown | "domain authority", "DA score", "authority assessment" |
| `entity-optimizer` | Entity recognition optimization for AI systems | URL + brand | Entity graph optimization recommendations | "entity optimization", "knowledge graph", "AI entity" |
| `memory-management` | Track SEO/GEO data over time | Historical data | Trend reports, comparisons | "track over time", "SEO history" |

---

## 2. Workflow Chains

### 2.1 Full GEO Audit Chain (Recommended Starting Point)

```
[URL Input]
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Discovery (Sequential)                           │
│  1. Fetch homepage HTML                                    │
│  2. Detect business type (SaaS/Local/E-commerce/Publisher) │
│  3. Extract key pages (sitemap or internal links, up to 50) │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Parallel Analysis (5 Subagents)                   │
│                                                             │
│  geo-ai-visibility  → AI Visibility Score (35%)            │
│     ├─ geo-citability (passage scoring)                    │
│     ├─ geo-crawlers (robots.txt analysis)                   │
│     ├─ geo-llmstxt (llms.txt analysis)                     │
│     └─ geo-brand-mentions (Wikipedia, Reddit, YouTube)      │
│                                                             │
│  geo-platform-analysis → Platform Readiness per platform    │
│     (Google AIO, ChatGPT, Perplexity, Gemini, Bing Copilot)│
│                                                             │
│  geo-technical → Technical Score (15%)                       │
│     (SSR, CWV, crawlability, security)                      │
│                                                             │
│  geo-content → Content Score (20%)                          │
│     (E-E-A-T, readability, AI content detection)            │
│                                                             │
│  geo-schema → Schema Score (10%)                            │
│     (JSON-LD detection, validation, generation)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Synthesis                                        │
│  1. Calculate composite GEO Score (0-100)                  │
│  2. Generate prioritized action plan                        │
│  3. Output: GEO-AUDIT-REPORT.md                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    [Optional PDF Generation]
                           │
                           ▼
                   GEO-REPORT.pdf (via ReportLab)
```

**Entry Point:** `/geo audit <url>`
**Output:** `GEO-AUDIT-REPORT.md` + optionally `GEO-REPORT.pdf`
**Blocking Points:** Business type ambiguity (offer user choice), 50+ location page threshold (require justification)

---

### 2.2 Full SEO Audit Chain

```
[URL Input]
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Business Type Detection                           │
│  SaaS / Local / E-commerce / Publisher / Agency / Other    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Parallel Subagent Analysis (7-12 agents)          │
│                                                             │
│  seo-technical ──→ Technical SEO Score (22%)              │
│  seo-content ────→ Content Quality Score (23%)             │
│  seo-schema ─────→ Schema Score (10%)                       │
│  seo-sitemap ─────→ Sitemap Quality                         │
│  seo-performance ─→ Core Web Vitals Score (10%)             │
│  seo-visual ──────→ Visual/Mobile Analysis (5%)            │
│  seo-geo ─────────→ AI Search Readiness (10%)               │
│  [seo-local] ────→ Local SEO Score (conditional)           │
│  [seo-maps] ─────→ Maps Health Score (conditional)         │
│  [seo-google] ───→ Google API Data (conditional)          │
│  [seo-dataforseo] → Live SERP Data (extension)             │
│  [seo-image-gen] ─→ Image Audit + Plan (extension)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Synthesis                                        │
│  1. Calculate SEO Health Score (0-100)                     │
│  2. Generate prioritized action plan                        │
│  3. Offer PDF report via seo-google                        │
└─────────────────────────────────────────────────────────────┘
```

**Entry Point:** `/seo audit <url>`
**Output:** Unified SEO Health Score + action plan
**Blocking Points:** Business type ambiguity, API credential detection (graceful degradation)

---

### 2.3 Content Creation + Optimization Chain

```
Keyword Research
    │ keyword-research
    ▼
┌──────────────┐
│ Keyword List │
│ Topic        │
│ Clusters     │
└──────┬───────┘
       │
       ▼
SERP Analysis
    │ serp-analysis
    ▼
┌──────────────┐
│ Content      │
│ Requirements │
│ SERP        │
│ Features    │
└──────┬───────┘
       │
       ▼
Content Gap Analysis (optional)
    │ content-gap-analysis
    ▼
┌──────────────┐
│ Missing     │
│ Topics      │
└──────┬───────┘
       │
       ▼
Content Creation
    │ seo-content-writer
    ▼
┌──────────────┐
│ Draft        │
│ Article      │
└──────┬───────┘
       │
       ▼
On-Page SEO Audit
    │ on-page-seo-auditor
    ▼
┌──────────────┐
│ Issues +    │
│ Recommend-  │
│ ations      │
└──────┬───────┘
       │
       ▼
Schema Generation
    │ schema-markup-generator
    ▼
┌──────────────┐
│ JSON-LD     │
│ Code        │
└──────┬───────┘
       │
       ▼
GEO Content Optimization
    │ geo-content-optimizer
    ▼
┌──────────────┐
│ High         │
│ Citability  │
│ Passages    │
└─────────────┘
```

**Entry Points:** `/keyword-research <topic>` or `/serp-analysis <keyword>`
**Output:** Published, optimized article

---

### 2.4 Local Business GEO/SEO Chain

```
URL Input
    │
    ▼
┌────────────────────────────────────────────┐
│  Business Detection                         │
│  - Brick-and-mortar vs SAB vs Hybrid        │
│  - Industry vertical (restaurant, legal...) │
└────────────────────┬───────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   [Local SEO Audit]    [Maps Intelligence]
   seo-local            seo-maps
   - GBP signals        - Geo-grid rank tracking
   - NAP consistency    - GBP completeness
   - Citations          - Review health
   - Local schema       - Competitor radius
          │                     │
          └──────────┬──────────┘
                     ▼
        ┌─────────────────────────┐
        │  Local SEO Health      │
        │  Score (0-100)        │
        └─────────────────────────┘
```

**Entry Point:** `/seo local <url>` or `/seo maps <command>`
**Blocking Points:** DataForSEO availability (Tier 0 vs Tier 1 capabilities differ significantly)

---

### 2.5 Technical SEO Deep-Dive Chain

```
URL Input
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  technical-seo-checker                                    │
│                                                          │
│  Crawlability ──→ Robots.txt, sitemaps, crawl errors    │
│  Indexability ──→ Canonicals, noindex, duplicates        │
│  Site Speed ─────→ CWV (LCP, INP, CLS), TTFB           │
│  Mobile ─────────→ Responsive, touch targets             │
│  Security ───────→ HTTPS, HSTS, CSP headers             │
│  URL Structure ──→ Redirect chains, clean URLs          │
│  Structured Data → Schema validation                     │
│  International ──→ Hreflang implementation               │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
              Technical Health Score (0-100)
              Critical / High / Medium / Low issues
              Implementation Roadmap
```

**Entry Point:** `/technical-seo-checker <url>` or `/seo technical <url>`
**Blocking Points:** None (all static analysis)

---

### 2.6 Rank Tracking & Monitoring Chain

```
URL + Keywords Input
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  rank-tracker                                            │
│  - Keyword position tracking over time                   │
│  - SERP feature tracking                                 │
│  - Competitor position monitoring                        │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
              Ranking Position Data
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  performance-reporter                                     │
│  - CWV trend tracking                                    │
│  - Speed metrics over time                               │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  backlink-monitor                                         │
│  - New/lost links tracking                               │
│  - Toxic link detection                                  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  alert-manager                                           │
│  - Configured alerts for ranking drops                   │
│  - Technical issue notifications                         │
└──────────────────────────────────────────────────────────┘
```

**Entry Point:** `/rank-tracker <keywords>` (continuous monitoring)
**Blocking Points:** API credentials for live data

---

## 3. Overlap & Integration Analysis

### 3.1 GEO vs SEO Skill Overlap Matrix

| Area | GEO Skill | SEO Skill | Overlap | Recommendation |
|------|-----------|-----------|---------|-----------------|
| Technical SEO | `geo-technical` | `seo-technical` | Both analyze crawlability, indexability, mobile, security, CWV | **Keep separate** — geo-technical is GEO-weighted (SSR critical for AI), seo-technical is comprehensive |
| Content Quality | `geo-content` | `seo-content` | Both assess E-E-A-T, readability | **Keep separate** — geo-content focuses on AI citability signals, seo-content on QRG compliance |
| Schema Markup | `geo-schema` | `seo-schema` | Same functionality | **Consolidate** — both detect/validate/generate JSON-LD; recommend `seo-schema` as canonical (more mature) |
| AI Crawler Access | `geo-crawlers` | `seo-geo` | Both check robots.txt for AI bots | **Consolidate** — `geo-crawlers` is more comprehensive; absorb into `seo-geo` as module |
| Citability | `geo-citability` | `seo-geo` | Passage-level citation analysis | **Keep separate** — `geo-citability` is atomic, used by `geo-ai-visibility` |
| Brand Mentions | `geo-brand-mentions` | None | Unique to GEO | N/A |
| Platform Optimization | `geo-platform-analysis` | None | Unique to GEO | N/A |
| llms.txt | `geo-llmstxt` | `seo-geo` | Both analyze/generate llms.txt | **Consolidate** — `geo-llmstxt` is more mature; absorb into `seo-geo` |
| Google APIs | None | `seo-google` | Google CrUX, GSC, GA4 | N/A |
| Maps Intelligence | None | `seo-maps`, `seo-local` | Local search optimization | N/A |

### 3.2 Atomic vs Composite Skill Classification

#### Atomic Skills (Cannot be split further)

| Skill | Justification |
|-------|---------------|
| `geo-citability` | Passage-level scoring is a single focused operation |
| `geo-crawlers` | Single robots.txt/header analysis operation |
| `geo-llmstxt` | Single llms.txt validation/generation |
| `geo-brand-mentions` | Single platform scanning operation |
| `keyword-research` | Single keyword discovery workflow |
| `serp-analysis` | Single SERP examination workflow |
| `backlink-analyzer` | Single backlink profile analysis |
| `content-gap-analysis` | Single gap identification workflow |
| `on-page-seo-auditor` | Single page audit (though multi-step internally) |
| `technical-seo-checker` | Single technical audit (multi-step internally) |

#### Composite Skills (Can be orchestrated from atomic skills)

| Skill | Composed Of | Orchestration Pattern |
|-------|-------------|----------------------|
| `geo` | geo-audit + 10 sub-skills | Sequential discovery → Parallel analysis → Synthesis |
| `geo-audit` | geo-ai-visibility, geo-platform-analysis, geo-technical, geo-content, geo-schema | Parallel subagent execution |
| `geo-ai-visibility` | geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions | Sequential within each dimension |
| `seo` | seo-technical, seo-content, seo-schema, seo-sitemap, seo-performance, seo-visual, seo-geo, seo-local, seo-maps, seo-google | Parallel subagent + conditional spawns |
| `geo-report` | All geo-audit outputs | Aggregation and formatting |
| `geo-report-pdf` | geo-report data | PDF generation |

### 3.3 Integration Recommendations

1. **Consolidate schema skills**: `seo-schema` and `geo-schema` have identical functionality. Recommend making `seo-schema` the canonical implementation and having `geo-schema` delegate to it.

2. **Merge llms.txt analysis**: `geo-llmstxt` should become a sub-skill called by `seo-geo` rather than only `geo-ai-visibility`.

3. **Standardize crawler access**: `geo-crawlers` should be called by both `geo-ai-visibility` (for GEO scoring) and `seo-technical` (for AI bot rules in robots.txt).

4. **Separate content and geo-content**: Despite overlap in E-E-A-T assessment, `geo-content` and `seo-content` serve different masters — AI citability vs QRG compliance. Keep both but ensure they use shared reference frameworks.

5. **Local SEO unified entry**: Both `seo-local` and `seo-maps` are local-specific. Consider a unified `/seo local <url>` that spawns both subagents rather than conditional spawning.

---

## 4. Automation Blockers & Default Resolution

### 4.1 Workflow Chain Blockers

| Workflow | Blocker Point | Default Resolution |
|----------|---------------|-------------------|
| Full GEO Audit | Business type ambiguity | Present top 2 detected types with signals; use most likely default |
| Full GEO Audit | 50+ location pages detected | Hard stop requiring explicit user justification |
| Full SEO Audit | Business type ambiguity | Same as GEO — present options, default to detected |
| Full SEO Audit | API credentials missing | Graceful degradation — skip API-dependent agents, note limitations |
| seo-maps | DataForSEO MCP unavailable | Tier 0 fallback — use free APIs (Nominatim, Overpass) with redistributed weights |
| seo-google | Google credentials missing | Tier 0 — use PageSpeed Insights public API, note limited data |
| seo-local | Not a local business | Skip local-specific checks silently |
| geo-report-pdf | Audit data missing | Require prior audit; prompt to run `/geo audit` first |
| keyword-research | No SEO tool API | Manual input mode — ask user for seed keywords and available data |
| serp-analysis | API limits | Fall back to WebFetch-based SERP observation |

### 4.2 Skill Invocation Blockers

| Skill | Blocker | Default |
|-------|---------|---------|
| `geo citability` | URL unreachable | Report error, suggest URL verification |
| `geo llmstxt` | Site doesn't exist | Report 404, do not generate placeholder |
| `geo brands` | Brand name ambiguous | Ask user to confirm exact brand name |
| `seo technical` | Timeout fetching large site | Cap at 50 pages, note crawl was partial |
| `seo geo` | DataForSEO MCP unavailable | Use static analysis only, note limited AI visibility data |
| `rank-tracker` | No keywords provided | Prompt user for keyword list |

### 4.3 Fully Automated Paths (No Human Confirmation Required)

These paths can run end-to-end without any blocking points:

1. **`/geo quick <url>`** — 60-second visibility snapshot (inline, no file output)
2. **`/geo page <url>`** — Single page GEO analysis (no business type detection needed)
3. **`/seo page <url>`** — Single page SEO analysis
4. **`/seo technical <url>`** — Full technical audit (no business type, no API needed)
5. **`/seo sitemap <url>`** — Sitemap analysis

### 4.4 Recommended Defaults for Full Automation

To achieve fully automated GEO/SEO workflows:

1. **Business type detection**: Default to "SaaS" if ambiguous (most common for tech companies being audited)
2. **Location page threshold**: Default to warning at 30+ pages, allow override flag to bypass hard stop
3. **API credentials missing**: Always proceed with static analysis; never block on missing API access
4. **PDF report generation**: Offer but don't require; default to markdown output
5. **DataForSEO unavailability**: Silently use free tier capabilities; never block on paid API access

---

## 5. Skill Metadata Summary

### 5.1 Skills by GEO Relevance

| GEO Relevance | Skills |
|--------------|--------|
| **Critical** (Direct GEO impact) | `geo`, `geo-audit`, `geo-ai-visibility`, `geo-citability`, `geo-platform-analysis`, `geo-platform-optimizer`, `geo-content`, `geo-schema`, `geo-report`, `geo-report-pdf` |
| **High** (Strong GEO impact) | `seo-geo`, `geo-crawlers`, `geo-llmstxt`, `serp-analysis`, `entity-optimizer` |
| **Medium** (Contributes to GEO) | `seo-content`, `geo-technical`, `keyword-research`, `on-page-seo-auditor`, `content-gap-analysis`, `geo-brand-mentions` |
| **Low** (Indirect GEO impact) | `seo-technical`, `seo-sitemap`, `seo-local`, `seo-maps`, `backlink-analyzer`, `domain-authority-auditor` |

### 5.2 Skills by Category

| Category | Count | Skills |
|----------|-------|--------|
| **Orchestrators** | 3 | `geo`, `seo`, `geo-audit` |
| **GEO Agents** | 5 | `geo-ai-visibility`, `geo-platform-analysis`, `geo-technical`, `geo-content`, `geo-schema` |
| **GEO Atomic** | 5 | `geo-citability`, `geo-crawlers`, `geo-llmstxt`, `geo-brand-mentions`, `geo-platform-optimizer` |
| **SEO Subagents** | 12 | `seo-technical`, `seo-content`, `seo-schema`, `seo-sitemap`, `seo-visual`, `seo-performance`, `seo-geo`, `seo-local`, `seo-maps`, `seo-google`, `seo-dataforseo`, `seo-image-gen` |
| **SEO Atomic (mktgs)** | 4 | `keyword-research`, `serp-analysis`, `backlink-analyzer`, `content-gap-analysis` |
| **Content** | 4 | `seo-content-writer`, `geo-content-optimizer`, `meta-tags-optimizer`, `content-gap-analysis` |
| **Optimization** | 5 | `on-page-seo-auditor`, `technical-seo-checker`, `internal-linking-optimizer`, `content-refresher`, `schema-markup-generator` |
| **Monitoring** | 4 | `rank-tracker`, `performance-reporter`, `backlink-monitor`, `alert-manager` |
| **Cross-cutting** | 4 | `content-quality-auditor`, `domain-authority-auditor`, `entity-optimizer`, `memory-management` |
| **Report Generation** | 2 | `geo-report`, `geo-report-pdf` |

### 5.3 Skills by Tool Dependencies

| Dependency | Skills |
|------------|--------|
| **WebFetch only** | `geo-citability`, `geo-crawlers`, `geo-llmstxt`, `geo-brand-mentions`, `on-page-seo-auditor`, `technical-seo-checker` |
| **Playwright** | `seo-visual` |
| **Google APIs** | `seo-google`, `seo-performance` |
| **DataForSEO MCP** | `seo-maps` (Tier 1), `seo-dataforseo` |
| **nanobanana-mcp** | `seo-image-gen` |
| **SEO Tool APIs (Ahrefs/SEMrush)** | `keyword-research`, `serp-analysis`, `backlink-analyzer`, `content-gap-analysis`, `rank-tracker` |
| **None (pure analysis)** | `geo-platform-analysis`, `geo-content`, `geo-schema`, `seo-technical`, `seo-content`, `seo-schema` |

---

## 6. Reference: All Available Skills by Invocation Name

### GEO Entry Points
- `/geo audit <url>` — Full GEO + SEO audit
- `/geo page <url>` — Single page GEO analysis
- `/geo citability <url>` — AI citability scoring
- `/geo crawlers <url>` — AI crawler access check
- `/geo llmstxt <url>` — llms.txt analysis/generation
- `/geo brands <url>` — Brand mention scanning
- `/geo platforms <url>` — Platform-specific optimization
- `/geo schema <url>` — Schema markup audit
- `/geo technical <url>` — Technical GEO/SEO audit
- `/geo content <url>` — Content quality E-E-A-T assessment
- `/geo report <url>` — Client-ready GEO report
- `/geo report-pdf <url>` — Professional PDF report
- `/geo quick <url>` — 60-second visibility snapshot

### SEO Entry Points
- `/seo audit <url>` — Full website SEO audit
- `/seo page <url>` — Single page SEO analysis
- `/seo sitemap <url or generate>` — XML sitemap analysis/generation
- `/seo schema <url>` — Schema markup detection/validation
- `/seo images <url>` — Image optimization analysis
- `/seo technical <url>` — Technical SEO audit
- `/seo content <url>` — E-E-A-T content analysis
- `/seo geo <url>` — AI Overviews/GEO optimization
- `/seo plan <business-type>` — Strategic SEO planning
- `/seo programmatic [url|plan]` — Programmatic SEO
- `/seo competitor-pages [url|generate]` — Competitor pages
- `/seo local <url>` — Local SEO analysis
- `/seo maps [command] [args]` — Maps intelligence
- `/seo hreflang [url]` — Hreflang/i18n audit
- `/seo google [command] [url]` — Google SEO APIs
- `/seo dataforseo [command]` — DataForSEO live data
- `/seo image-gen [use-case] <description>` — Image generation plan

### Marketing Entry Points
- `/keyword-research` — Keyword discovery and clustering
- `/serp-analysis` — SERP feature and ranking analysis
- `/backlink-analyzer` — Backlink profile analysis
- `/content-gap-analysis` — Competitor content gap identification
- `/on-page-seo-auditor` — On-page SEO audit
- `/technical-seo-checker` — Technical SEO health check
- `/schema-markup` — Schema markup generator
- `/rank-tracker` — Keyword ranking monitoring
- `/performance-reporter` — CWV and speed tracking
- `/content-quality-auditor` — E-E-A-T benchmark audit
- `/domain-authority-auditor` — DA scoring (CITE framework)
- `/entity-optimizer` — Entity recognition optimization
