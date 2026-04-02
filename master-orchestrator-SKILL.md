---
name: seo-geo-master-orchestrator
description: Master orchestration skill for fully automated SEO+GEO optimization workflows. Use when the user wants comprehensive site optimization, AI visibility improvement, or keyword-driven content optimization. Triggers on phrases like "优化我的独立站" (optimize my independent site), "做关键词研究" (do keyword research), "检查 AI 可见度" (check AI visibility), "SEO audit", "GEO audit", "rank higher", "AI citations", "full optimization", or any request combining SEO and GEO goals. Handles multi-skill routing, parallel execution, data format standardization, and result aggregation into unified reports.
license: CC BY-NC-SA 4.0
version: 1.0.0
tags: [seo, geo, orchestrator, automation, ai-search, keyword-research]
trigger-conditions:
  - url-provided
  - keyword-research-requested
  - ai-visibility-requested
  - full-site-audit-requested
  - competitor-analysis-requested
allowed-tools:
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

# SEO+GEO Master Orchestrator

## Purpose

This skill serves as the central orchestrator that routes user requests to the correct SEO/GEO sub-skills, executes them in appropriate sequences or parallel batches, standardizes data interchange between skills, and aggregates results into unified, actionable reports. It implements a **silent execution protocol** — never asking for confirmation, using defaults for missing data, and generating full output in a single pass.

## Silent Execution Protocol

```
1. DO NOT ask for confirmation at any step.
2. Use reasonable defaults for any missing input data.
3. Generate full output in one pass — no iterative "should I continue?" prompts.
4. If a sub-skill fails, log the failure, apply fallback logic, and continue.
5. Always produce a complete report even if partial data is unavailable.
6. Track execution metrics for evolution engine integration.
```

---

## Part 1: Intent Recognition Router

### 1.1 Trigger Word Matrix

| Category | Trigger Words (EN) | Trigger Words (ZH) | Routing Target |
|---|---|---|---|
| **Full Audit** | "audit my site", "full SEO", "complete audit", "SEO health", "site audit", "diagnose my site" | "完整审计", "全站审计", "网站诊断", "优化我的独立站" | Workflow A |
| **Keyword Research** | "keyword research", "find keywords", "keyword analysis", "search volume", "keyword opportunities" | "关键词研究", "关键词分析", "找关键词" | Workflow B (Phase 1) |
| **AI Visibility** | "AI visibility", "GEO", "AI citations", "AI mentions", "LLMO", "check AI visibility", "AI search visibility" | "AI可见度", "GEO", "AI引用", "AI提及" | Workflow C |
| **Content Optimization** | "optimize content", "improve rankings", "content gap", "SERPs", "on-page SEO" | "内容优化", "提升排名" | Workflow B |
| **Technical SEO** | "technical SEO", "crawl errors", "indexing", "sitemap", "robots.txt", "Core Web Vitals" | "技术SEO", "爬虫错误", "索引问题" | seo-technical |
| **Competitor Analysis** | "competitor analysis", "who ranks for", "competing pages", "competitive analysis" | "竞品分析", "竞争对手" | seo-competitor-pages |
| **Schema Markup** | "schema", "structured data", "rich results", "JSON-LD" | "Schema", "结构化数据" | seo-schema |
| **Local SEO** | "local SEO", "Google Maps", "near me", "local business" | "本地SEO", "谷歌地图" | seo-local, seo-maps |
| **Images** | "image SEO", "image optimization", "alt text", "image compression" | "图片SEO", "图片优化" | seo-images, seo-image-gen |
| **Programmatic SEO** | "programmatic SEO", "pages at scale", "bulk pages", "template pages" | "程序化SEO", "批量页面" | seo-programmatic |
| **Link Building** | "backlinks", "link building", "domain authority", "external links" | "外链", "链接建设", "域名权重" | backlink-analyzer, domain-authority-auditor |
| **Sitemap** | "sitemap", "XML sitemap", "site map" | "网站地图", "sitemap" | seo-sitemap |
| **Hreflang** | "hreflang", "international SEO", "language targeting" | "hreflang", "国际化SEO" | seo-hreflang |
| **E-E-A-T** | "E-E-A-T", "author authority", "expertise", "trustworthiness" | "E-E-A-T", "专业权威" | seo-content |
| **SERP Features** | "SERP features", "featured snippets", "People Also Ask", "rich results" | "SERP功能", "精选摘要" | serp-analysis |
| **Internal Linking** | "internal links", "site architecture", "link structure", "navigation" | "内链", "网站结构", "导航" | internal-linking-optimizer, site-architecture |
| **GEO Brand** | "brand mentions", "brand visibility", "brand authority", "YouTube presence" | "品牌提及", "品牌权威", "品牌可见度" | geo-brand-mentions |
| **GEO Platform** | "platform optimization", "Reddit", "Wikipedia", "LinkedIn presence" | "平台优化", "Reddit", "维基百科" | geo-platform-optimizer |
| **GEO Content** | "GEO content", "AI-friendly content", "citation optimization" | "GEO内容", "AI友好内容" | geo-content |
| **GEO Technical** | "llms.txt", "AI crawlers", "robots.txt for AI" | "llms.txt", "AI爬虫" | geo-technical |
| **GEO Schema** | "GEO schema", "entity schema", "Organization schema" | "GEO Schema", "实体Schema" | geo-schema |
| **Report Generation** | "report", "export", "PDF report", "summary" | "报告", "导出", "PDF报告" | geo-report, geo-report-pdf |

### 1.2 Fallback Logic

```
IF no trigger words matched:
  → Default to Workflow A (Full Audit) with URL provided by user
  → If no URL provided, ask once for URL then proceed

IF multiple categories matched:
  → Prioritize by specificity: Full Audit > AI Visibility > Keyword Research > others
  → Execute highest-priority workflow

IF user provides URL only (no other context):
  → Default to Workflow A (Full Audit)

IF user provides URL + keyword(s):
  → Default to Workflow B (Keyword-Driven Content Optimization)

IF user provides brand/entity name + URL:
  → Default to Workflow C (GEO AI Visibility)

IF request is ambiguous:
  → Attempt Workflow A, include all sections marked [EXPANDABLE]
```

---

## Part 2: Standardized Data Formats

### 2.1 Skill Input Schema (JSON)

```json
{
  "task": {
    "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | SINGLE_SKILL",
    "intent": "string",
    "priority": "HIGH | MEDIUM | LOW",
    "options": {
      "parallel": true,
      "timeout_per_skill_ms": 60000,
      "continue_on_error": true
    }
  },
  "inputs": {
    "url": "https://example.com",
    "keywords": ["keyword1", "keyword2"],
    "brand_name": "Brand Name",
    "competitor_urls": ["https://competitor1.com"],
    "language": "en | zh | auto",
    "scope": "full | partial"
  },
  "context": {
    "business_type": "saas | ecommerce | publisher | local | agency | hybrid",
    "target_audience": "string",
    "geographic_target": "string"
  }
}
```

### 2.2 Skill Output Schema (JSON)

```json
{
  "skill_id": "string",
  "status": "SUCCESS | PARTIAL | FAILED",
  "score": 0-100,
  "findings": [
    {
      "issue": "string",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "impact": "string",
      "evidence": "string",
      "fix": "string",
      "page_url": "string (optional)"
    }
  ],
  "metrics": {
    "pages_analyzed": 0,
    "issues_found": 0,
    "execution_time_ms": 0
  },
  "raw_data": {},
  "errors": ["string (if any)"]
}
```

### 2.3 Aggregation Schema

```json
{
  "orchestrator_version": "1.0.0",
  "execution_timestamp": "ISO8601",
  "workflow_executed": "WORKFLOW_A",
  "overall_score": 0-100,
  "skill_results": [
    { "skill": "seo-audit", "status": "SUCCESS", "score": 75, "findings": [...] },
    { "skill": "geo-audit", "status": "SUCCESS", "score": 62, "findings": [...] }
  ],
  "aggregated_findings": [
    { "issue": "...", "severity": "HIGH", "source_skills": ["seo-audit", "geo-technical"] }
  ],
  "execution_metrics": {
    "total_time_ms": 0,
    "skills_invoked": 0,
    "skills_succeeded": 0,
    "skills_failed": 0
  }
}
```

### 2.4 Error Propagation Format

```json
{
  "error": {
    "source_skill": "string",
    "error_code": "TIMEOUT | BLOCKED | NOT_FOUND | PARSE_ERROR | NETWORK_ERROR",
    "message": "Human-readable error description",
    "fallback_applied": "true | false",
    "fallback_action": "SKIPPED | DEFAULT_VALUE | RETRY | SKIP_SKILL"
  }
}
```

---

## Part 3: Core Workflow Templates

### Workflow A — Full SEO+GEO Site Audit

**Input:** URL  
**Output:** `FULL-AUDIT-REPORT.md`  
**Execution Time:** ~15-25 minutes (parallel sub-skills)  

#### Phase A1: Site Discovery & Classification (Sequential)

```
1. WebFetch homepage → detect business_type
2. Attempt /sitemap.xml → extract up to 50 URLs
3. If no sitemap → crawl homepage + 2 levels of internal links
4. Respect robots.txt directives
5. Classify: SaaS | E-commerce | Publisher | Local | Agency | Hybrid
6. Save: site_map.json + business_classification.json
```

#### Phase A2: Parallel Sub-Skill Execution

```
INVOKE seo-technical (parallel)
  → robots.txt, HTTPS, Core Web Vitals, crawlability, indexability

INVOKE seo-content (parallel)
  → E-E-A-T signals, content quality, thin content detection

INVOKE seo-schema (parallel)
  → Schema.org markup validation, missing opportunities

INVOKE seo-competitor-pages (parallel)
  → Identify top 3 competitors from SERP for core keywords

INVOKE geo-audit (parallel)
  → AI citability, brand authority, technical GEO, E-E-A-T for AI

INVOKE geo-brand-mentions (parallel)
  → YouTube, Reddit, Wikipedia, LinkedIn presence analysis
```

#### Phase A3: Score Aggregation

```
SEO_Score = weighted average of:
  - Technical SEO (30%)
  - Content Quality (25%)
  - Schema Markup (15%)
  - Competitor Position (15%)
  - On-Page Optimization (15%)

GEO_Score = weighted average of:
  - AI Citability (25%)
  - Brand Authority (20%)
  - Content E-E-A-T (20%)
  - Technical GEO (15%)
  - Schema & Structured Data (10%)
  - Platform Optimization (10%)

Combined_Score = (SEO_Score * 0.6) + (GEO_Score * 0.4)
```

#### Phase A4: Report Generation

**Output file:** `FULL-AUDIT-REPORT.md`

```
Sections:
1. Executive Summary (Combined Score, top 5 wins, top 5 critical issues)
2. SEO Score Breakdown + Findings (by severity)
3. GEO Score Breakdown + Findings (by severity)
4. Business-Type-Specific Recommendations
5. Quick Wins (implement this week)
6. 30-Day Action Plan (organized by theme/week)
7. Appendix: Pages Analyzed, Tools Used, Data Sources
```

#### Edge Cases (Workflow A)

| Blockage | Default Action |
|---|---|
| URL returns 5xx | Skip page, note in appendix, continue with available pages |
| No sitemap found | Fall back to link crawling from homepage (max 50 pages) |
| Robots.txt blocks crawling | Note blocked paths, audit only accessible pages |
| Sub-skill times out (>60s) | Log timeout, return PARTIAL status, use cached/default scores |
| No competitor keywords | Skip competitor analysis, weight redistributed to other categories |
| Site is JavaScript-heavy | Note rendering concerns, flag for seo-technical follow-up |

---

### Workflow B — Keyword-Driven Content Optimization

**Input:** URL + Keywords (array)  
**Output:** `KEYWORD-OPTIMIZATION-REPORT.md` + optimized content drafts  
**Execution Time:** ~10-20 minutes  

#### Phase B1: Keyword Research & SERP Analysis

```
1. INVOKE keyword-research (for each keyword in array)
   → Search volume, competition, CPC, related terms

2. INVOKE serp-analysis (for each keyword)
   → SERP features present, competitor titles/descriptions, intent classification

3. INVOKE content-gap-analysis
   → What does the site currently rank for vs. what it should
   → Topical authority gaps
```

#### Phase B2: Content Audit for Target Keywords

```
1. For each target keyword:
   - Check current ranking position (approximate via SERP analysis)
   - Audit pages targeting this keyword (title, H1, content, internal links)
   - Identify content gaps vs. top-ranking competitors

2. INVOKE seo-page (per page, if specific pages identified)
   → On-page SEO audit for each targeted page
```

#### Phase B3: Content Optimization

```
1. For each keyword with content gaps:
   - Generate content optimization brief
   - INVOKE seo-content → produce optimized content outline
   - INVOKE seo-schema → identify schema opportunities for this content

2. For each keyword with ranking opportunities:
   - Generate title tag + meta description variations
   - Generate heading structure recommendations
   - Generate internal linking recommendations
```

#### Phase B4: Schema & Technical Reinforcement

```
1. INVOKE seo-schema
   → For each piece of content, recommend schema types:
     - HowTo schema for tutorials
     - FAQPage schema for Q&A content
     - Article schema for blog posts
     - Product schema for e-commerce

2. INVOKE seo-technical
   → Check page speed for target pages
   → Verify canonical tags are correct
   → Check internal link equity to target pages
```

#### Phase B5: Tracking Plan

```
1. Define tracking metrics:
   - Target keyword ranking positions (weekly check)
   - Organic traffic to optimized pages (30-day baseline)
   - SERP feature capture rate

2. Generate tracking spreadsheet template
3. Set up geo-report entry for AI citation tracking
```

#### Edge Cases (Workflow B)

| Blockage | Default Action |
|---|---|
| Keyword has zero search volume | Flag as low-priority, still optimize but de-emphasize |
| Competitor pages are extremely strong | Recommend 6-month content plan vs. quick wins |
| No existing pages target the keyword | Generate new content brief, flag for content creation |
| SERP data unavailable | Use keyword-research tool data only, note limitations |

---

### Workflow C — GEO AI Visibility Enhancement

**Input:** URL + Brand/Entity Name  
**Output:** `GEO-VISIBILITY-PLAN.md` + AI citation tracking report  
**Execution Time:** ~10-15 minutes  

#### Phase C1: AI Visibility Assessment

```
1. INVOKE seo-geo-analyzer
   → Current AI citability score
   → AI crawler access analysis
   → LLM-friendly content assessment

2. INVOKE geo-citability
   → Passage-level citability scoring
   → Answer block quality evaluation
   → Statistical/data density analysis
```

#### Phase C2: Citation Opportunity Identification

```
1. Search AI responses (via WebFetch to Perplexity/ChatGPT search)
   → For brand entity queries: "What is [Brand]?", "[Brand] alternatives"
   → For product queries: "[Product] vs competitors"
   → For category queries: "Best [category] tools/services"

2. INVOKE geo-brand-mentions
   → Check where brand is mentioned across AI-training data sources
   → YouTube, Reddit, Wikipedia, LinkedIn, news sites

3. INVOKE geo-platform-optimizer
   → Score platform presence (0-100 per platform)
   → Identify missing high-value platforms
```

#### Phase C3: Entity & Content Optimization

```
1. INVOKE geo-schema
   → Verify Organization schema completeness
   → Check for Person schema (founder/CEO if applicable)
   → Add ClaimReview schema if applicable
   → Strengthen EntitySchema for brand

2. INVOKE geo-content
   → Optimize content for AI citation:
     - Add quotable passages with statistics
     - Create FAQ-style answer blocks
     - Strengthen E-E-A-T signals in content
   → Generate entity reference pages

3. INVOKE geo-technical
   → Check/create llms.txt
   → Verify AI crawler access in robots.txt
   → Audit for rendering/accessibility issues
```

#### Phase C4: Citation Tracking Setup

```
1. Create AI citation tracking spreadsheet:
   - Monitor monthly: AI response inclusions for brand queries
   - Track: Perplexity, ChatGPT (Browse), Claude web search
   - Metrics: Mention count, citation rank, sentiment

2. INVOKE geo-report
   → Generate GEO progress report template
   → Set baseline metrics for re-measurement
```

#### Edge Cases (Workflow C)

| Blockage | Default Action |
|---|---|
| Brand has zero AI presence | Start from zero, recommend 90-day GEO foundation build |
| llms.txt already exists | Audit quality, recommend improvements vs. creation |
| No statistical data in content | Recommend adding 3-5 key statistics to improve citability |
| Platform accounts don't exist | Prioritize YouTube + Reddit as highest-impact new platforms |

---

## Part 4: Parallel Execution Strategy

### 4.1 Skill Grouping for Parallel Invocation

```
Group 1 (Always Parallel):
  - seo-technical
  - geo-audit
  - geo-brand-mentions
  - seo-schema
  - seo-content

Group 2 (Sequential after Group 1):
  - seo-competitor-pages (depends on Group 1 for baseline)
  - geo-platform-optimizer (depends on geo-brand-mentions)

Group 3 (Sequential — report aggregation):
  - geo-report (aggregates all GEO scores)
  - Report generation (aggregates all findings)
```

### 4.2 Concurrency Limits

```
MAX_PARALLEL_SKILLS = 5
MAX_CONCURRENT_WEBFETCHES = 3
SKILL_TIMEOUT_MS = 60000
WEBFETCH_TIMEOUT_MS = 30000
```

### 4.3 Result Collection Protocol

```
FOR each parallel skill invocation:
  1. Start skill with task payload (Skill Input Schema)
  2. Wait for completion or timeout
  3. Collect result in Aggregation Schema format
  4. On timeout: log error, assign score = 50 (PARTIAL), continue

AFTER all parallel skills complete:
  1. Aggregate all findings by severity
  2. Deduplicate overlapping findings (same issue from multiple skills)
  3. Calculate weighted overall scores
  4. Generate unified report
```

---

## Part 5: Evolution Engine Interface

### 5.1 Execution Metrics Log

```json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C",
  "inputs": { "url": "...", "keywords": [...], "brand_name": "..." },
  "metrics": {
    "total_execution_time_ms": 0,
    "skills_invoked": 0,
    "skills_succeeded": 0,
    "skills_failed": 0,
    "pages_crawled": 0,
    "findings_total": 0,
    "findings_by_severity": { "critical": 0, "high": 0, "medium": 0, "low": 0 }
  },
  "scores": {
    "overall_score": 0,
    "seo_score": 0,
    "geo_score": 0,
    "category_scores": {}
  },
  "user_feedback": null
}
```

### 5.2 Evolution Engine Hook

After each workflow execution, write execution metrics to:

**File:** `seekr/evolution-metrics/<execution_id>.json`

This file is consumed by the Evolution Engine to:
- Identify which skills consistently underperform
- Detect common blockage patterns
- Suggest workflow optimizations
- Track score improvements over time

### 5.3 Optimization Suggestion Protocol

```
IF skill failure rate > 20%:
  → Log: "Skill [X] failing at elevated rate — investigate"

IF average workflow time exceeds 30 minutes:
  → Log: "Performance degradation detected — optimize parallelization"

IF user provides feedback on output quality:
  → Log feedback to execution_metrics.user_feedback field
  → Forward to Evolution Engine for workflow tuning
```

---

## Part 6: Edge Case Registry

### 6.1 Universal Fallbacks (All Workflows)

| Scenario | Fallback Action |
|---|---|
| URL not accessible | Return FAILED status, generate report noting URL inaccessible |
| Partial data available | Execute with available data, mark affected sections [INCOMPLETE] |
| No keywords provided for Workflow B | Use homepage content to extract top 5 keyword opportunities |
| No brand name for Workflow C | Extract from homepage title/org schema |
| Non-HTML content (PDF/media) | Skip crawling, note in appendix |
| Rate limiting during crawl | Back off 5 seconds, retry once, then skip |
| Context window near limit | Truncate lowest-priority findings, note [TRUNCATED] |

### 6.2 Workflow-Specific Edge Cases

**Workflow A:**
- If SEO Score < 30: Recommend starting with seo-technical before other skills
- If GEO Score < 30: Recommend starting with geo-technical before geo-content
- If business_type = "Hybrid": Run both relevant vertical workflows in parallel

**Workflow B:**
- If keyword competition is "Extremely High": Recommend long-tail variant approach
- If no existing content for keyword: Generate content brief via seo-content-writer
- If target page has no-index: Flag as blocking issue before content optimization

**Workflow C:**
- If brand has Wikipedia page: Check for accuracy, note citation opportunities there
- If brand is B2B: Prioritize LinkedIn + industry forums over YouTube
- If brand is B2C: Prioritize Reddit + Instagram + YouTube over LinkedIn

---

## Part 7: Report Output Templates

### 7.1 Full Audit Report (Workflow A)

```
# Full SEO+GEO Audit Report: [Site Name]

**Date:** [ISO8601]
**URL:** [URL]
**Business Type:** [Detected]
**Pages Analyzed:** [Count]
**Overall Score:** [X]/100 (SEO: [X] | GEO: [X])

---

## Executive Summary

[2-3 paragraph synthesis of SEO + GEO health, top strengths, critical gaps]

## Combined Scorecard

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| SEO Foundation | [X]/100 | 60% | [X] |
| GEO Foundation | [X]/100 | 40% | [X] |
| **Combined Score** | | | **[X]/100** |

## SEO Findings

### Critical Issues
[...]

### High Priority
[...]

### Medium Priority
[...]

### Low Priority
[...]

## GEO Findings

### Critical Issues
[...]

### High Priority
[...]

### Medium Priority
[...]

### Low Priority
[...]

## Quick Wins (This Week)

1. [Actionable item with expected impact]
2. [...]

## 30-Day Action Plan

### Week 1: Technical Foundation
- [ ] [...]

### Week 2: Content & GEO
- [ ] [...]

### Week 3: Optimization
- [ ] [...]

### Week 4: Authority Building
- [ ] [...]

## Appendix
- Pages Analyzed
- Tools Invoked
- Data Sources
```

### 7.2 Keyword Optimization Report (Workflow B)

```
# Keyword Optimization Report: [Site Name]

**Date:** [ISO8601]
**Target Keywords:** [List]
**Current Average Position:** [X]

---

## Keyword Opportunity Matrix

| Keyword | Volume | Difficulty | Intent | Opportunity |
|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] |

## Content Gap Analysis

[What competitors rank for that you don't]

## Page-Level Recommendations

### [Page URL]
- **Target Keyword:** [...]
- **Current Title:** [...]
- **Recommended Title:** [...]
- **Current Meta:** [...]
- **Recommended Meta:** [...]
- **Heading Adjustments:** [...]
- **Internal Link Opportunities:** [...]

## Content Briefs (For New Pages)

[Detailed briefs for content that should be created]

## Schema Recommendations

[Schema types to add per page]

## Tracking Plan

[Metrics to monitor, check frequency]
```

### 7.3 GEO Visibility Plan (Workflow C)

```
# GEO AI Visibility Plan: [Brand Name]

**Date:** [ISO8601]
**Current AI Visibility Score:** [X]/100
**Target Score (90 days):** [X]/100

---

## AI Citation Landscape

[Where AI systems currently cite/mention the brand]

## Platform Presence Audit

| Platform | Status | Current Score | Action |
|---|---|---|---|
| YouTube | [Present/Missing] | [X]/100 | [...] |
| Reddit | [...] | [...] | [...] |
| Wikipedia | [...] | [...] | [...] |
| LinkedIn | [...] | [...] | [...] |

## Entity Optimization

[Organization schema improvements, Person schema additions]

## Content Optimization for AI

### High-Citability Passages to Add
[Specific passage recommendations]

### FAQ Blocks to Add
[Question-answer pairs optimized for AI extraction]

### E-E-A-T Signals to Strengthen
[Author credentials, citations, data points to add]

## Citation Tracking

[Monthly check cadence, tools to use]

## 90-Day GEO Roadmap

### Days 1-30: Foundation
- [Actions]

### Days 31-60: Authority
- [Actions]

### Days 61-90: Visibility
- [Actions]
```

---

## Part 8: Skill Routing Reference Table

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT ROUTING MAP                        │
├──────────────────┬──────────────────────────────────────────┤
│ URL only         │ → Workflow A (Full Audit)                 │
│ URL + Keywords   │ → Workflow B (Keyword Optimization)       │
│ URL + Brand      │ → Workflow C (GEO Visibility)             │
│ URL + Keywords   │ → Workflow B                             │
│   + Brand        │ → Workflow B + C combined                 │
│ "check AI        │ → Workflow C                             │
│  visibility"     │                                          │
│ "audit my site"  │ → Workflow A                             │
│ "why not ranking"│ → Workflow A                             │
│ "keyword research│ → Workflow B Phase 1 only                │
│  only"           │                                          │
│ "competitor"     │ → seo-competitor-pages (single skill)    │
│ "technical SEO"  │ → seo-technical (single skill)          │
│ "schema markup"  │ → seo-schema (single skill)             │
│ "backlinks"      │ → backlink-analyzer (single skill)       │
│ "internal links" │ → internal-linking-optimizer (single)    │
│ "local SEO"      │ → seo-local + seo-maps                   │
│ "images"         │ → seo-images + seo-image-gen             │
│ "programmatic"   │ → seo-programmatic (single skill)        │
│ "E-E-A-T"        │ → seo-content (single skill)             │
│ "GEO report"     │ → geo-report (single skill)              │
│ "export PDF"     │ → geo-report-pdf (single skill)          │
└──────────────────┴──────────────────────────────────────────┘
```

---

## Part 9: Version & Maintenance

```
Version: 1.0.0
Created: 2026-04-03
Last Updated: 2026-04-03

Change Log:
- 1.0.0: Initial release with 3 core workflows (A/B/C), intent router,
         standardized data formats, and evolution engine interface

Dependencies:
- seo-audit, seo-technical, seo-content, seo-schema, seo-competitor-pages
- seo-plan, seo-page, seo-programmatic, seo-images, seo-image-gen
- seo-local, seo-maps, seo-google, seo-hreflang, seo-dataforseo
- seo-geo, seo-geo-analyzer, seo-content-writer
- geo-audit, geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions
- geo-platform-optimizer, geo-schema, geo-technical, geo-content
- geo-report, geo-report-pdf
- keyword-research, serp-analysis, backlink-analyzer, competitor-analysis
- content-gap-analysis, website-analyzer, schema-markup, meta-tags-optimizer
- rank-tracker, performance-reporter, internal-linking-optimizer
- domain-authority-auditor, site-architecture

Evolution Engine Integration:
- Metrics file path: seekr/evolution-metrics/<execution_id>.json
- Feedback field: user_feedback (nullable string)
- Schedule: Write metrics after every workflow execution
```
