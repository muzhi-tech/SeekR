---
name: seekr
description: |
  Master orchestration skill for fully automated SEO+GEO optimization of English independent sites.
  Triggers on: audit requests ("audit my site", "优化我的独立站"), keyword research, AI visibility checks,
  or full optimization workflows. Executes four workflows in sequence or parallel:
    A. Full site SEO+GEO audit (URL → full audit report with SHEEP/GEM scoring)
    B. Keyword-driven content optimization (URL + keywords → optimized pages)
    C. GEO AI visibility enhancement (URL + brand → GEO visibility plan)
    D. GEO article auto-generation (keyword → publish-ready .md file with SEO+GEO+Schema)
  After daily audit (Workflow A), automatically triggers Workflow D for high-opportunity keywords.
  Never asks for confirmation. Uses defaults for all missing data. Generates complete output in one pass.
license: CC BY-NC-SA 4.0
version: 1.0.0
tags: [seo, geo, orchestrator, automation, ai-search, keyword-research, content-generation, independent-sites, english]
trigger-conditions:
  - url-provided
  - keyword-research-requested
  - ai-visibility-requested
  - full-site-audit-requested
  - competitor-analysis-requested
  - geo-article-requested
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

This skill serves as the central orchestrator that:
1. Routes user requests to the correct SEO/GEO sub-skills via intent recognition
2. Executes workflows in appropriate sequences or parallel batches
3. Runs geo_optimizer.py (SHEEP framework) to score every execution
4. Aggregates results into unified reports
5. Automatically triggers GEO article generation (Workflow D) after daily audits
6. Writes execution metrics to evolution-metrics/ for the Evolution Engine

**Silent execution protocol — never ask, never stop, always complete.**

## Silent Execution Protocol

```
1. DO NOT ask for confirmation at any step.
2. Use reasonable defaults for any missing input data.
3. Generate full output in one pass — no iterative "should I continue?" prompts.
4. If a sub-skill fails, log the failure, apply fallback logic, and continue.
5. Always produce a complete report even if partial data is unavailable.
6. Track execution metrics (SHEEP scores) for evolution engine integration.
```

---

## Part 1: Intent Recognition Router

### 1.1 Trigger Word Matrix

| Category | Trigger Words (EN) | Trigger Words (ZH) | Routing Target |
|---|---|---|---|
| **Full Audit** | "audit my site", "full SEO", "complete audit", "SEO health", "site audit", "diagnose my site" | "完整审计", "全站审计", "网站诊断", "优化我的独立站" | Workflow A |
| **Keyword Research** | "keyword research", "find keywords", "keyword analysis", "search volume", "keyword opportunities" | "关键词研究", "关键词分析", "找关键词" | Workflow B (Phase 1) |
| **AI Visibility** | "AI visibility", "GEO", "AI citations", "AI mentions", "LLMO", "check AI visibility" | "AI可见度", "GEO", "AI引用" | Workflow C |
| **Content Optimization** | "optimize content", "improve rankings", "content gap", "SERPs", "on-page SEO" | "内容优化", "提升排名" | Workflow B |
| **GEO Article** | "write article", "generate content", "create post", "GEO article", "SEO article", "write for me" | "写文章", "生成内容", "GEO文章" | Workflow D |
| **Technical SEO** | "technical SEO", "crawl errors", "indexing", "sitemap", "robots.txt", "Core Web Vitals" | "技术SEO", "爬虫错误", "索引问题" | seo-technical |
| **Competitor Analysis** | "competitor analysis", "who ranks for", "competing pages", "competitive analysis" | "竞品分析", "竞争对手" | seo-competitor-pages |
| **Schema Markup** | "schema", "structured data", "rich results", "JSON-LD" | "Schema", "结构化数据" | seo-schema |
| **Local SEO** | "local SEO", "Google Maps", "near me", "local business" | "本地SEO", "谷歌地图" | seo-local, seo-maps |
| **Images** | "image SEO", "image optimization", "alt text" | "图片SEO", "图片优化" | seo-images, seo-image-gen |
| **Link Building** | "backlinks", "link building", "domain authority", "external links" | "外链", "链接建设" | backlink-analyzer |
| **E-E-A-T** | "E-E-A-T", "author authority", "expertise", "trustworthiness" | "E-E-A-T", "专业权威" | seo-content |
| **SERP Features** | "SERP features", "featured snippets", "People Also Ask", "rich results" | "SERP功能", "精选摘要" | serp-analysis |
| **Internal Linking** | "internal links", "site architecture", "link structure" | "内链", "网站结构" | internal-linking-optimizer |
| **GEO Brand** | "brand mentions", "brand visibility", "brand authority", "YouTube presence" | "品牌提及", "品牌权威" | geo-brand-mentions |
| **GEO Platform** | "platform optimization", "Reddit", "Wikipedia", "LinkedIn presence" | "平台优化", "Reddit" | geo-platform-optimizer |
| **GEO Content** | "GEO content", "AI-friendly content", "citation optimization" | "GEO内容", "AI友好内容" | geo-content |
| **GEO Technical** | "llms.txt", "AI crawlers", "robots.txt for AI" | "llms.txt", "AI爬虫" | geo-technical |
| **Report Generation** | "report", "export", "PDF report", "summary" | "报告", "导出", "PDF报告" | geo-report, geo-report-pdf |

### 1.2 Fallback Logic

```
IF no trigger words matched:
  → Default to Workflow A (Full Audit) with URL provided by user
  → If no URL provided, ask once for URL then proceed

IF multiple categories matched:
  → Prioritize by specificity: Full Audit > GEO Article > AI Visibility > Keyword Research > others
  → Execute highest-priority workflow

IF user provides URL only (no other context):
  → Default to Workflow A (Full Audit)

IF user provides URL + keyword(s):
  → Default to Workflow B (Keyword-Driven Content Optimization)

IF user provides brand/entity name + URL:
  → Default to Workflow C (GEO AI Visibility)

IF user provides keyword(s) only:
  → Default to Workflow D (GEO Article Generation)

IF request is ambiguous:
  → Attempt Workflow A, include all sections marked [EXPANDABLE]
```

---

## Part 2: Standardized Data Formats

### 2.1 Skill Input Schema (JSON)

```json
{
  "task": {
    "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | WORKFLOW_D | SINGLE_SKILL",
    "intent": "string",
    "priority": "HIGH | MEDIUM | LOW",
    "options": {
      "parallel": true,
      "timeout_per_skill_ms": 60000,
      "continue_on_error": true,
      "auto_trigger_workflow_d": true
    }
  },
  "inputs": {
    "url": "https://example.com",
    "keywords": ["keyword1", "keyword2"],
    "brand_name": "Brand Name",
    "competitor_urls": ["https://competitor1.com"],
    "language": "en",
    "scope": "full | partial",
    "target_market": "english"
  },
  "context": {
    "business_type": "saas | ecommerce | publisher | local | agency | hybrid",
    "target_audience": "string",
    "geographic_target": "global | us | uk | au"
  }
}
```

### 2.2 Skill Output Schema (JSON)

```json
{
  "skill_id": "string",
  "status": "SUCCESS | PARTIAL | FAILED",
  "score": 0-100,
  "sheep_scores": {
    "S_semantic_coverage": { "raw": 0-100, "weight": 0.25 },
    "H_human_credibility": { "raw": 0-100, "weight": 0.25 },
    "E1_evidence_structuring": { "raw": 0-100, "weight": 0.20 },
    "E2_ecosystem_integration": { "raw": 0-100, "weight": 0.15 },
    "P_performance_monitoring": { "raw": 0-100, "weight": 0.15 }
  },
  "gem_score": 0-100,
  "findings": [
    {
      "issue": "string",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "impact": "string",
      "evidence": "string",
      "fix": "string",
      "sheep_dimension": "S | H | E1 | E2 | P"
    }
  ],
  "metrics": {
    "pages_analyzed": 0,
    "issues_found": 0,
    "execution_time_ms": 0
  },
  "errors": ["string (if any)"]
}
```

### 2.3 Aggregation Schema

```json
{
  "orchestrator_version": "1.0.0",
  "execution_timestamp": "ISO8601",
  "workflow_executed": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | WORKFLOW_D",
  "overall_score": 0-100,
  "gem_score": 0-100,
  "sheep_scores": {
    "S_semantic_coverage": 0-100,
    "H_human_credibility": 0-100,
    "E1_evidence_structuring": 0-100,
    "E2_ecosystem_integration": 0-100,
    "P_performance_monitoring": 0-100
  },
  "skill_results": [
    { "skill": "seo-audit", "status": "SUCCESS", "score": 75, "findings": [...] }
  ],
  "aggregated_findings": [
    { "issue": "...", "severity": "HIGH", "source_skills": ["seo-audit", "geo-technical"], "sheep_dimension": "H" }
  ],
  "workflow_d_output": {
    "article_keywords": ["string"],
    "article_file": "seekr/articles/<keyword>-<date>.md",
    "gem_score": 0-100
  },
  "execution_metrics": {
    "total_time_ms": 0,
    "skills_invoked": 0,
    "skills_succeeded": 0,
    "skills_failed": 0
  }
}
```

---

## Part 3: Core Workflow Templates

### Workflow A — Full SEO+GEO Site Audit

**Input:** URL
**Output:** `FULL-AUDIT-REPORT.md` + `evolution-metrics/<execution_id>.json`
**Execution Time:** ~15-25 minutes
**Auto-trigger:** After completion, automatically queues Workflow D for high-opportunity keywords detected

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

#### Phase A3: SHEEP Scoring (via geo_optimizer.py)

```
Run: python geo_optimizer.py <analyzed_html_file> --format json
Extract: { S, H, E1, E2, P } scores → calculate GEM score
Write: evolution-metrics/<execution_id>.json
```

#### Phase A4: Score Aggregation

```
SEO_Score = weighted average of:
  - Technical SEO (30%)
  - Content Quality (25%)
  - Schema Markup (15%)
  - Competitor Position (15%)
  - On-Page Optimization (15%)

GEO_Score (SHEEP-based) = weighted average of:
  - S_semantic_coverage (25%)
  - H_human_credibility (25%)
  - E1_evidence_structuring (20%)
  - E2_ecosystem_integration (15%)
  - P_performance_monitoring (15%)

Combined_Score = (SEO_Score * 0.6) + (GEM_Score * 0.4)
```

#### Phase A5: Report Generation + Workflow D Trigger

```
Output: FULL-AUDIT-REPORT.md
  - Executive Summary
  - SEO Score Breakdown + Findings
  - GEO Score Breakdown (SHEEP dimensions)
  - Quick Wins (implement this week)
  - 30-Day Action Plan

Auto-detect high-opportunity keywords from audit:
  → keywords with high search volume + low competition
  → keywords where competitor ranks but site doesn't
  → Auto-queue: Workflow D for each high-opportunity keyword
  → Generate: seekr/articles/<keyword>-<date>.md
```

#### Edge Cases (Workflow A)

| Blockage | Default Action |
|---|---|
| URL returns 5xx | Skip page, note in appendix, continue with available pages |
| No sitemap found | Fall back to link crawling from homepage (max 50 pages) |
| Robots.txt blocks crawling | Note blocked paths, audit only accessible pages |
| Sub-skill times out (>60s) | Log timeout, return PARTIAL status, use cached/default scores |
| No competitor keywords | Skip competitor analysis, redistribute weights |
| Site is JavaScript-heavy | Note rendering concerns, flag for seo-technical follow-up |
| Daily audit complete | **Auto-trigger Workflow D** for high-opportunity keywords found |

---

### Workflow B — Keyword-Driven Content Optimization

**Input:** URL + Keywords (array)
**Output:** `KEYWORD-OPTIMIZATION-REPORT.md` + optimized content briefs
**Execution Time:** ~10-20 minutes

#### Phase B1: Keyword Research & SERP Analysis

```
1. INVOKE keyword-research (for each keyword)
   → Search volume, competition, CPC, related terms, intent classification

2. INVOKE serp-analysis (for each keyword)
   → SERP features present, competitor titles/descriptions, intent classification

3. INVOKE content-gap-analysis
   → What the site currently ranks for vs. what it should
   → Topical authority gaps
```

#### Phase B2: Content Audit for Target Keywords

```
For each target keyword:
  - Check current ranking position (approximate via SERP analysis)
  - Audit pages targeting this keyword (title, H1, content, internal links)
  - Identify content gaps vs. top-ranking competitors

INVOKE seo-page (per page, if specific pages identified)
```

#### Phase B3: Content Optimization Briefs

```
For each keyword with content gaps:
  - Generate content optimization brief
  - INVOKE seo-content → produce optimized content outline
  - INVOKE seo-schema → identify schema opportunities

For each keyword with ranking opportunities:
  - Generate title tag + meta description variations
  - Generate heading structure recommendations
  - Generate internal linking recommendations
```

#### Phase B4: Schema & Technical Reinforcement

```
INVOKE seo-schema
  → HowTo schema for tutorials
  → FAQPage schema for Q&A content
  → Article schema for blog posts
  → Product schema for e-commerce

INVOKE seo-technical
  → Check page speed for target pages
  → Verify canonical tags
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
| No existing pages target the keyword | Generate new content brief, flag for Workflow D |
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

3. INVOKE geo-technical
   → Check/create llms.txt
   → Verify AI crawler access in robots.txt
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

### Workflow D — GEO Article Auto-Generation (Daily Audit → Content)

**Input:** Keyword(s) from Workflow A audit output (high-opportunity keywords)
**Output:** `seekr/articles/<keyword>-<date>.md` — publish-ready GEO-optimized article
**Execution Time:** ~10-15 minutes per article
**Trigger:** Automatically after Workflow A completes (daily audit cycle)

#### Phase D1: Keyword Research (from Audit Output)

```
1. Receive high-opportunity keywords from Workflow A audit
   → keywords with high search volume + low competition
   → keywords where competitors rank but site doesn't
   → "content gaps" identified during audit

2. For each keyword, INVOKE keyword-research
   → Confirm search volume, keyword difficulty, CPC
   → Classify intent: informational / commercial / transactional

3. INVOKE serp-analysis
   → Analyze top 5 ranking pages for this keyword
   → Extract: titles, H2s, word count, schema used, content structure
   → Identify: SERP features (featured snippet, People Also Ask, video)
```

#### Phase D2: Content Gap Analysis

```
INVOKE content-gap-analysis
  → What topics do top-ranking pages cover that our article doesn't?
  → What unique angle can we add (statistics, expert quotes, fresh data)?

Determine article angle:
  → If no existing article: create comprehensive "ultimate guide"
  → If existing thin content: create "significantly better version"
  → Target: 2000-3000 words (ChatGPT optimal: 1500-2500)
```

#### Phase D3: GEO-Optimized Article Writing (seo-content-writer)

```
Generate article with the following structure:

# [Target Keyword] — The Definitive Guide/[Year]

## Introduction (150 words max, direct answer first)
→ Answer the main question in the first paragraph
→ Include: what, why, how in first 150 words (Google AI Overview target)
→ End with: "In this guide, you'll learn..."

## [H2: Core Topic Section]
### [H3: Sub-point 1]
Content with:
  - [STATISTIC_PLACEHOLDER: +41% 引用效果] — add real statistic
  - [EXPERT_QUOTE: source, year] — add expert citation
  - Statistics formatted as: "According to [source], [exact figure]" (higher citability)

### [H3: Sub-point 2]
### [H3: Sub-point 3]

## [H2: How-To / Step-by-Step Section]
[Numbered list or step-by-step — high citation probability]

## [H2: FAQ Section]
[6-8 questions from People Also Ask + additional common questions]
→ Format as Question: Answer (both schema and content)

## [H2: Expert Analysis / Data Section]
- 3-5 statistics with source citations
- Data tables where applicable
- Charts/visual placeholders [INSERT CHART: type]

## Conclusion
→ Summary of key takeaways
→ Call to action

---

[// JSON-LD will be appended at end of file]
```

#### Phase D4: Page SEO Optimization

```
INVOKE meta-tags-optimizer (via seo-content-writer or direct)
  → Title: [Primary Keyword] — [Benefit] | [Brand]
  → Meta description: [160 chars, includes keyword + CTA]
  → URL slug: /[primary-keyword]/ (clean, hyphenated)

INVOKE internal-linking-optimizer
  → Identify 3-5 existing pages to link from/to new article
  → Generate anchor text suggestions
```

#### Phase D5: Schema Markup Generation

```
INVOKE schema-markup-generator
  Output JSON-LD blocks:

  1. Article Schema:
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "[Article Title]",
    "author": { "@type": "Person", "name": "[Author Name]", "url": "[Author Page]" },
    "datePublished": "[YYYY-MM-DD]",
    "dateModified": "[YYYY-MM-DD]",
    "publisher": { "@type": "Organization", "name": "[Brand]" },
    "mainEntityOfPage": { "@type": "WebPage", "@id": "[URL]" }
  }

  2. FAQPage Schema (if FAQ section included):
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      { "@type": "Question", "name": "[Q1]", "acceptedAnswer": { "@type": "Answer", "text": "[A1]" } },
      ...
    ]
  }

  3. BreadcrumbList Schema (for navigation context)

  4. [Optional] HowTo Schema (if step-by-step section included)
```

#### Phase D6: GEO Content Optimization (geo-content-optimizer)

```
For each major section, rewrite paragraphs to maximize AI citability:

1. Add quotable passages:
   → "According to [authoritative source], [exact statistic with number]"
   → "[Exact figure]% of [audience] [action/finding]" (stronger than "many")

2. Strengthen E-E-A-T signals:
   → Add author credential block after introduction
   → Add "Last updated: [date]" with specific date
   → Add citation to method/sources section

3. Add FAQ blocks (3-5 questions):
   → Format: **Q: [Question]?** A: [Direct answer in 50-100 words]

4. Ensure Perplexity optimization:
   → H2 → H3 → bullet structure (40% more citations)
   → [1], [2] inline citation placeholders
   → "As of [recent date]" freshness markers

5. Ensure Google AI Overview optimization:
   → First 150 words contain direct, complete answer
   → Use "is" / "are" / "can" / "does" sentence starters
   → Include table or list where appropriate
```

#### Phase D7: Final Output & Tracking Setup

```
OUTPUT FILE: seekr/articles/<keyword-slug>-<YYYY-MM-DD>.md

File structure:
---
title: "[Article Title]"
date: YYYY-MM-DD
keyword: "[Primary Keyword]"
target_market: english
gem_score_target: 75
---

# [Article Title]

[Full article content with H2/H3 structure]

[// INLINE JSON-LD: Article Schema]
<script type="application/ld+json">
{ Article Schema JSON }
</script>

[// INLINE JSON-LD: FAQPage Schema]
<script type="application/ld+json">
{ FAQPage Schema JSON }
</script>

---

TRACKING SETUP:
1. Add keywords to rank-tracker config
2. Set content freshness reminder: 30 days
3. Log article URL in geo-report for citation tracking
4. Write execution metrics to evolution-metrics/<execution_id>.json
```

#### Edge Cases (Workflow D)

| Blockage | Default Action |
|---|---|
| No high-opportunity keywords from audit | Skip Workflow D, note "No article opportunities found" |
| Keyword extremely competitive | Generate article anyway but recommend long-tail variant angle |
| SERP data unavailable | Use keyword-research data, note limitations in article |
| Article file already exists for keyword | Append "-v2" suffix, do not overwrite existing |
| Language is not English | Use english as default, note "English content only" |
| Word count target unmet (<1500 words) | Expand FAQ section or add expert analysis section |
| External API rate limited | Continue with cached/previous data, note in metrics |

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

---

## Part 5: Evolution Engine Interface

### 5.1 Execution Metrics Log

Every workflow execution writes to `seekr/evolution-metrics/<execution_id>.json`:

```json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "workflow": "WORKFLOW_A | WORKFLOW_B | WORKFLOW_C | WORKFLOW_D",
  "inputs": { "url": "...", "keywords": [...], "brand_name": "..." },
  "sheep_scores": {
    "S_semantic_coverage": { "raw": 0-100, "weight": 0.25 },
    "H_human_credibility": { "raw": 0-100, "weight": 0.25 },
    "E1_evidence_structuring": { "raw": 0-100, "weight": 0.20 },
    "E2_ecosystem_integration": { "raw": 0-100, "weight": 0.15 },
    "P_performance_monitoring": { "raw": 0-100, "weight": 0.15 }
  },
  "gem_score": 0-100,
  "metrics": {
    "total_execution_time_ms": 0,
    "skills_invoked": 0,
    "skills_succeeded": 0,
    "skills_failed": 0,
    "pages_crawled": 0,
    "findings_total": 0,
    "articles_generated": 0
  },
  "workflow_d_output": {
    "articles_generated": ["seekr/articles/keyword1-date.md"],
    "keywords_targeted": ["keyword1", "keyword2"]
  },
  "user_feedback": null
}
```

### 5.2 Evolution Engine Hook

Metrics file consumed by seo-geo-evolution-engine for:
- Identifying skills that consistently underperform (low sheep scores)
- Detecting common blockage patterns (timeouts, API limits)
- Suggesting workflow optimizations (parallelization, deduplication)
- Tracking score improvements over time (GEM trend)
- Generating A/B test candidates for workflow optimization

---

## Part 6: Edge Case Registry

### 6.1 Universal Fallbacks (All Workflows)

| Scenario | Fallback Action |
|---|---|
| URL not accessible | Return FAILED status, generate report noting URL inaccessible |
| Partial data available | Execute with available data, mark affected sections [INCOMPLETE] |
| No keywords provided for Workflow D | Use homepage content to extract top 5 keyword opportunities |
| Non-HTML content (PDF/media) | Skip crawling, note in appendix |
| Rate limiting during crawl | Back off 5 seconds, retry once, then skip |
| Context window near limit | Truncate lowest-priority findings, note [TRUNCATED] |

### 6.2 Workflow-Specific Edge Cases

**Workflow A:**
- If GEM Score < 30: Recommend starting with geo-technical before other skills
- If GEM Score < 30: Recommend starting with geo-content before geo-audit
- If business_type = "Hybrid": Run both relevant vertical workflows in parallel

**Workflow B:**
- If keyword competition is "Extremely High": Recommend long-tail variant approach
- If no existing content for keyword: Generate content brief, queue for Workflow D
- If target page has no-index: Flag as blocking issue before content optimization

**Workflow C:**
- If brand has Wikipedia page: Check for accuracy, note citation opportunities there
- If brand is B2B: Prioritize LinkedIn + industry forums over YouTube
- If brand is B2C: Prioritize Reddit + Instagram + YouTube over LinkedIn

**Workflow D:**
- If article already exists for keyword: Generate v2, do not overwrite
- If no article opportunities found in audit: Skip D silently, log note
- If target market is non-English: Default to English, note in metadata

---

## Part 7: Report Output Templates

### 7.1 Full Audit Report (Workflow A)

```
# Full SEO+GEO Audit Report: [Site Name]

**Date:** [ISO8601]
**URL:** [URL]
**Business Type:** [Detected]
**Pages Analyzed:** [Count]
**Overall Score:** [X]/100 (SEO: [X] | GEM: [X])

---

## Executive Summary

[2-3 paragraph synthesis of SEO + GEO health, top strengths, critical gaps]

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

## GEO Findings (SHEEP Dimensions)

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

## GEO Article Opportunities (Auto-Generated via Workflow D)

| Keyword | Search Volume | Competition | Article Angle | Status |
|---|---|---|---|---|
| [keyword] | [vol] | [low/med/high] | [angle] | [Queued/Generated] |

## Appendix
- Pages Analyzed
- Tools Invoked
- Data Sources
```

### 7.2 GEO Article Output Template (Workflow D)

See Part 3, Workflow D, Phase D7 for full file structure.

---

## Part 8: Version & Maintenance

```
Version: 1.0.0
Created: 2026-04-03
Last Updated: 2026-04-03

Change Log:
- 1.0.0: Initial release with 4 workflows (A/B/C/D), SHEEP/GEM scoring,
         intent router, standardized data formats, and evolution engine interface

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
- seo-content-writer (for Workflow D)

Evolution Engine Integration:
- Metrics file path: seekr/evolution-metrics/<execution_id>.json
- SHEEP scores: S(25%), H(25%), E1(20%), E2(15%), P(15%)
- Auto-trigger: Workflow D runs after every Workflow A completion
- Target market: English independent sites only
```
