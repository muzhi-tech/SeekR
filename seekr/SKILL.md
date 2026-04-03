---
name: seekr
version: "1.0.0"
description: |
  SeekR - Autonomous SEO + GEO Agent for English independent sites.
  Master orchestration skill that routes requests to appropriate sub-skills,
  executes four workflows (Audit/Keyword/AI Visibility/Article Generation),
  and scores results using SHEEP/GEM framework. Triggers on audit requests,
  keyword research, AI visibility checks, or full optimization workflows.
license: CC BY-NC-SA 4.0
compatibility: "Claude Code ≥1.0"
metadata:
  author: muzhi-tech
  geo-relevance: high
  target-market: english
  tags:
    - seo
    - geo
    - orchestrator
    - automation
    - ai-search
    - keyword-research
    - content-generation
    - independent-sites
    - english
triggers:
  - "audit my site"
  - "SEO audit"
  - "GEO"
  - "AI visibility"
  - "keyword research"
  - "优化我的独立站"
  - "GEO文章"
  - "write article"
  - "generate content"
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Write
  - Edit
  - Agent
  - Skill
---

# SeekR - SEO+GEO Master Orchestrator

## Purpose

SeekR is the **central orchestrator** for automated SEO+GEO optimization of English independent sites. It:
1. Routes user requests to correct sub-skills via intent recognition
2. Executes workflows in sequence or parallel batches
3. Scores every execution using SHEEP/GEM framework
4. Aggregates results into unified reports
5. Auto-triggers GEO article generation after daily audits
6. Writes execution metrics for the Evolution Engine

**Silent execution protocol — never ask, never stop, always complete.**

## Intent Recognition Router

### Trigger Word Matrix

| Category | EN Triggers | ZH Triggers | Workflow |
|---|---|---|---|
| **Full Audit** | "audit my site", "full SEO", "complete audit", "SEO health" | "完整审计", "全站审计", "优化独立站" | Workflow A |
| **Keyword Research** | "keyword research", "find keywords", "keyword analysis" | "关键词研究", "找关键词" | Workflow B |
| **AI Visibility** | "AI visibility", "GEO", "AI citations", "LLMO" | "AI可见度", "GEO" | Workflow C |
| **GEO Article** | "write article", "generate content", "GEO article" | "写文章", "GEO文章" | Workflow D |
| **Technical SEO** | "technical SEO", "crawl errors", "indexing" | "技术SEO", "爬虫错误" | seo-technical |
| **Schema** | "schema", "structured data", "JSON-LD" | "Schema", "结构化数据" | seo-schema |
| **Competitor** | "competitor analysis", "who ranks for" | "竞品分析", "竞争对手" | seo-competitor-pages |
| **E-E-A-T** | "E-E-A-T", "author authority", "expertise" | "E-E-A-T", "专业权威" | seo-content |
| **GEO Brand** | "brand mentions", "brand visibility", "YouTube" | "品牌提及", "品牌权威" | geo-brand-mentions |
| **GEO Technical** | "llms.txt", "AI crawlers", "robots.txt for AI" | "llms.txt", "AI爬虫" | geo-technical |

### Fallback Logic

```
IF no trigger words matched:
  → Default to Workflow A (Full Audit) with URL provided

IF user provides URL only:
  → Default to Workflow A (Full Audit)

IF user provides URL + keywords:
  → Default to Workflow B (Keyword-Driven Content Optimization)

IF user provides brand/entity name + URL:
  → Default to Workflow C (GEO AI Visibility)

IF user provides keyword(s) only:
  → Default to Workflow D (GEO Article Generation)
```

## SHEEP Framework Scoring

| Dimension | Full Name | Weight |
|---|---|---|
| **S** | Semantic Coverage | 25% |
| **H** | Human Credibility | 25% |
| **E1** | Evidence Structuring | 20% |
| **E2** | Ecosystem Integration | 15% |
| **P** | Performance Monitoring | 15% |

**GEM Score** = weighted average of all SHEEP dimensions (0-100)

---

## Workflow A — Full SEO+GEO Site Audit

**Input:** URL
**Output:** `FULL-AUDIT-REPORT.md` + execution metrics

### Phase A1: Site Discovery
```
1. WebFetch homepage → detect business_type
2. Attempt /sitemap.xml → extract up to 50 URLs
3. If no sitemap → crawl homepage + 2 levels
4. Respect robots.txt directives
5. Classify: SaaS | E-commerce | Publisher | Local | Agency | Hybrid
```

### Phase A2: Parallel Sub-Skill Execution
```
INVOKE seo-technical (parallel)
INVOKE seo-content (parallel)
INVOKE seo-schema (parallel)
INVOKE seo-competitor-pages (parallel)
INVOKE geo-audit (parallel)
INVOKE geo-brand-mentions (parallel)
```

### Phase A3: SHEEP Scoring
```
Run: python geo_optimizer.py <file> --format json
Extract: { S, H, E1, E2, P } scores → calculate GEM
Write: evolution-metrics/<execution_id>.json
```

### Phase A4: Report Generation
```
Output: FULL-AUDIT-REPORT.md
  - Executive Summary
  - SEO Score Breakdown + Findings
  - GEO Score Breakdown (SHEEP dimensions)
  - Quick Wins (implement this week)
  - 30-Day Action Plan

Auto-detect high-opportunity keywords → Auto-queue Workflow D
```

### Edge Cases (Workflow A)

| Blockage | Default Action |
|---|---|
| URL returns 5xx | Skip page, note in appendix, continue |
| No sitemap found | Fall back to link crawling (max 50 pages) |
| Sub-skill times out (>60s) | Log timeout, return PARTIAL status |
| Daily audit complete | **Auto-trigger Workflow D** for high-opportunity keywords |

---

## Workflow B — Keyword-Driven Content Optimization

**Input:** URL + Keywords (array)
**Output:** `KEYWORD-OPTIMIZATION-REPORT.md`

### Phase B1: Keyword Research & SERP Analysis
```
INVOKE keyword-research (per keyword)
INVOKE serp-analysis (per keyword)
INVOKE content-gap-analysis
```

### Phase B2: Content Audit for Target Keywords
```
- Check current ranking position
- Audit pages targeting this keyword
- Identify content gaps vs. competitors
```

### Phase B3: Content Optimization Briefs
```
- Generate content optimization brief
- INVOKE seo-content → optimized content outline
- INVOKE seo-schema → schema opportunities
```

### Phase B4: Tracking Plan
```
1. Define tracking metrics
2. Generate tracking spreadsheet template
3. Set up geo-report entry for AI citation tracking
```

---

## Workflow C — GEO AI Visibility Enhancement

**Input:** URL + Brand/Entity Name
**Output:** `GEO-VISIBILITY-PLAN.md`

### Phase C1: AI Visibility Assessment
```
INVOKE seo-geo-analyzer
INVOKE geo-citability
```

### Phase C2: Citation Opportunity Identification
```
1. Search AI responses (Perplexity/ChatGPT)
2. INVOKE geo-brand-mentions
3. INVOKE geo-platform-optimizer
```

### Phase C3: Entity & Content Optimization
```
INVOKE geo-schema → Organization/Person schema
INVOKE geo-content → Optimize for AI citation
INVOKE geo-technical → Check/create llms.txt
```

### Phase C4: Citation Tracking Setup
```
Create AI citation tracking spreadsheet
INVOKE geo-report → Generate GEO progress report
```

---

## Workflow D — GEO Article Auto-Generation

**Input:** Keyword(s) from Workflow A output
**Output:** `seekr/articles/<keyword>-<date>.md`

### Phase D1: Keyword Research (from Audit)
```
INVOKE keyword-research → Confirm volume, difficulty, CPC
INVOKE serp-analysis → Analyze top 5 ranking pages
```

### Phase D2: Content Gap Analysis
```
INVOKE content-gap-analysis
Determine article angle:
  - No existing article → comprehensive "ultimate guide"
  - Thin content exists → significantly better version
  - Target: 2000-3000 words
```

### Phase D3: GEO-Optimized Article Writing
```
Generate article structure:

# [Target Keyword] — The Definitive Guide/[Year]

## Introduction (150 words max, direct answer first)

## [H2: Core Topic Section]
### [H3: Sub-point with statistics]

## [H2: How-To / Step-by-Step Section]

## [H2: FAQ Section]
6-8 questions from People Also Ask

## [H2: Expert Analysis / Data Section]
3-5 statistics with source citations

## Conclusion
```

### Phase D4: Schema Markup
```
INVOKE schema-markup-generator
Output JSON-LD:
  1. Article Schema
  2. FAQPage Schema (if FAQ section)
  3. BreadcrumbList Schema
```

### Phase D5: GEO Content Optimization
```
- Add quotable passages with statistics
- Strengthen E-E-A-T signals
- Add FAQ blocks (3-5 questions)
- Ensure Perplexity optimization (H2→H3→bullet)
- Ensure Google AI Overview (first 150 words direct answer)
```

---

## Report Output Template

```
# Full SEO+GEO Audit Report: [Site Name]

**Date:** [ISO8601]
**URL:** [URL]
**Business Type:** [Detected]
**Overall Score:** [X]/100 (SEO: [X] | GEM: [X])

---

## Executive Summary

[2-3 paragraph synthesis of SEO + GEO health]

## SHEEP Score Breakdown

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| S - Semantic Coverage | [X]/100 | 25% | [X] |
| H - Human Credibility | [X]/100 | 25% | [X] |
| E1 - Evidence Structuring | [X]/100 | 20% | [X] |
| E2 - Ecosystem Integration | [X]/100 | 15% | [X] |
| P - Performance Monitoring | [X]/100 | 15% | [X] |
| **GEM Score** | | | **[X]/100** |

## SEO Findings

[Findings grouped by severity]

## GEO Findings (SHEEP)

[Findings grouped by SHEEP dimension]

## Quick Wins (This Week)

1. [Actionable item]

## 30-Day Action Plan

### Week 1: Technical Foundation
- [ ]

### Week 2: Content & GEO
- [ ]

### Week 3: Optimization
- [ ]

### Week 4: Authority Building
- [ ]
```

---

## Example Usage

```
用户: 帮我审计 https://example.com 的SEO和GEO

Claude: 正在执行SeekR全站审计...

1. 获取sitemap.xml...
2. 分析主要页面...
3. 执行并行子技能...
   - seo-technical ✓
   - seo-content ✓
   - seo-schema ✓
   - geo-audit ✓
   - geo-brand-mentions ✓
4. 计算SHEEP评分...
5. 生成优化建议...

═══════════════════════════════════════
  SEO+GEO Audit Report: example.com
═══════════════════════════════════════

GEM Score: 72/100 (B级)

SHEEP Breakdown:
  S: 75  H: 68  E1: 72  E2: 70  P: 78

Quick Wins:
  1. 添加FAQ Schema到产品页
  2. 更新90天未更新的博客内容
  3. 添加作者凭证到所有文章

自动触发: 正在为高机会关键词生成GEO文章...
```

---

## Related Skills

- `seo-technical` - Technical SEO audit
- `seo-content` - Content quality & E-E-A-T
- `seo-schema` - Schema markup validation
- `geo-audit` - AI citability audit
- `geo-brand-mentions` - Brand presence analysis
- `seekr-evolve` - Self-evolution engine
