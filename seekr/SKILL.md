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

---

## Phase 0 — Skill Dependency Pre-flight Check

**MANDATORY: Run this phase BEFORE executing any workflow (A/B/C/D).**

```bash
python seekr/install.py              # Check all dependencies (<2s)
python seekr/install.py --install    # Auto-install missing skills
python seekr/install.py --workflow A # Check one workflow only
```

```
IF 0 missing → proceed to Intent Recognition
IF missing remain → Skill tool with skill="find-skills" args="<skill-name>"
IF critical (seo-technical, geo-audit) unavailable → inform user, proceed with available only
```

Fallback (install.py unavailable): Use Glob to verify `~/.claude/skills/<name>/SKILL.md` exists.

---

## Intent Recognition Router

### Trigger Word Matrix

> Detailed routing rules with priority and pattern matching: see `seekr/references/trigger_rules.json`

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
URL only → Workflow A | URL + keywords → B | Brand + URL → C | Keywords only → D
No match → Default to Workflow A (Full Audit)
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

| Blockage | Action |
|---|---|
| URL 5xx | Skip page, note, continue |
| No sitemap | Crawl links (max 50 pages) |
| Sub-skill timeout (>60s) | Log, return PARTIAL |
| Daily audit done | **Auto-trigger Workflow D** |

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

### Phase B2: Content Audit
```
Check ranking → Audit targeting pages → Identify content gaps vs. competitors
```

### Phase B3: Optimization Briefs
```
Generate brief → INVOKE seo-content (outline) → INVOKE seo-schema (opportunities)
```

### Phase B4: Tracking Plan
```
Define metrics → Generate tracking template → Set up geo-report for AI citation tracking
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

### Phase C2: Citation Opportunities
```
Search AI responses (Perplexity/ChatGPT) → INVOKE geo-brand-mentions → INVOKE geo-platform-optimizer
```

### Phase C3: Entity & Content
```
INVOKE geo-schema (Organization/Person) → geo-content (AI citation) → geo-technical (llms.txt)
```

### Phase C4: Tracking Setup
```
Create citation tracking spreadsheet → INVOKE geo-report → GEO progress report
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
Structure: Title → Introduction (150w, direct answer) → Core H2+H3 → How-To → FAQ (6-8 PAA) → Expert Data (3-5 stats) → Conclusion
Target: 2000-3000 words
```

### Phase D4: Schema Markup
```
INVOKE schema-markup-generator → JSON-LD: Article, FAQPage, BreadcrumbList
```

### Phase D5: GEO Optimization
```
Quotable stats + E-E-A-T signals + FAQ blocks + Perplexity (H2→H3→bullet) + AI Overview (150w direct answer)
```

---

## Report Output Template

→ 使用 `seekr/references/report-template.md` 作为报告输出模板

---

## Example Usage

```
用户: 帮我审计 https://example.com 的SEO和GEO

Claude: 正在执行SeekR全站审计...
1. 获取sitemap.xml → 48 URLs
2. 执行并行子技能 → seo-technical ✓ seo-content ✓ geo-audit ✓
3. SHEEP评分 → S:75 H:68 E1:72 E2:70 P:78 → GEM: 72/100
4. Quick Wins: 添加FAQ Schema, 更新博客内容, 添加作者凭证
5. 自动触发 Workflow D → 生成GEO文章...
```

---

## Related Skills

- `seo-technical` - Technical SEO audit
- `geo-audit` - AI citability audit
- `seekr-evolve` - Self-evolution engine
- 完整列表见 `SKILLS-REGISTRY.json`
