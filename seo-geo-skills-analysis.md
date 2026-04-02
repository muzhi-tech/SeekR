# SEO/GEO Skills 清单分析与工作流映射

## 1. Skills 分类地图（技能矩阵）

### 1.1 按功能维度分类

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SEO/GEO Skills 生态全景                                 │
├──────────────────┬────────────────────────────────────────────────────────────────┤
│   类别            │   Skills                                                    │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│ 顶层编排器         │ seo (skills/seo/)                                           │
│                   │ geo (skills/geo/)                                           │
│                   │ seo-geo-analyzer (skills/seo-geo-analyzer/)                  │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│ GEO 核心 (agents)  │ geo-ai-visibility                                           │
│                   │ geo-content                                                  │
│                   │ geo-platform-analysis                                        │
│                   │ geo-schema                                                   │
│                   │ geo-technical                                                │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│ SEO 分析 (agents)  │ seo-technical, seo-content, seo-schema                      │
│                   │ seo-local, seo-maps, seo-google                             │
│                   │ seo-audit, seo-page, seo-sitemap, seo-images                │
│                   │ seo-visual, seo-plan, seo-programmatic                      │
│                   │ seo-competitor-pages, seo-hreflang                          │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│ GEO 子技能 (skills)│ geo-audit, geo-citability, geo-crawlers                    │
│                   │ geo-llmstxt, geo-brand-mentions, geo-platform-optimizer     │
│                   │ geo-schema, geo-technical, geo-content, geo-report           │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│ 扩展技能           │ seo-dataforseo, seo-image-gen                               │
│                   │ ai-seo                                                      │
└──────────────────┴────────────────────────────────────────────────────────────────┘
```

### 1.2 技能矩阵详解

#### A. 顶层编排器 (Orchestrators)

| Skill | 职责 | 触发关键词 | 子组件数 | 特点 |
|-------|------|-----------|---------|------|
| **seo** | SEO 分析主入口，GEO 为辅 | "seo", "audit", "sitemap", "E-E-A-T", "AI Overviews" | 17 子技能 | 全面但以 SEO 为主 |
| **geo** | GEO 分析主入口，SEO 为辅 | "geo", "AI search", "citability", "llms.txt" | 10 子技能 + 5 子代理 | GEO-first, SEO-supported |
| **seo-geo-analyzer** | 独立 SEO/GEO 分析 | "分析 SEO", "GEO分析" | 12 维度框架 | 中文界面，独立实现 |

#### B. 核心分析 Agents (agents/)

| Agent | 职责 | 输入 | 输出 | 覆盖维度 |
|-------|------|------|------|---------|
| **geo-ai-visibility** | AI 可见度综合分析 | URL | AI Visibility Score, Citability, Crawler Access, Brand Mentions | 4/5 |
| **geo-content** | 内容质量/E-E-A-T | URL | Content Score, E-E-A-T 4维度, Readability, AI Content Assessment | 8/10 |
| **geo-platform-analysis** | 平台特定优化 | URL | Google AIO, ChatGPT, Perplexity, Gemini, Bing Copilot 各平台评分 | 5 平台 |
| **geo-schema** | Schema 检测/验证/生成 | URL | Schema Score, JSON-LD templates, Validation results | 9 schema 类型 |
| **geo-technical** | 技术 SEO | URL | Technical Score (9 categories), SSR/CSR Assessment | 9 categories |

#### C. 子技能 (skills/geo-*/)

| Skill | 职责 | 与 Agent 关系 |
|-------|------|--------------|
| geo-audit | 完整 GEO 审计编排 | 使用 geo-ai-visibility 等 5 个 agents |
| geo-citability | 段落级 AI 引用就绪度 | 是 geo-ai-visibility 的子集 |
| geo-crawlers | AI 爬虫访问检查 | 是 geo-ai-visibility 的子集 |
| geo-llmstxt | llms.txt 分析/生成 | 是 geo-ai-visibility 的子集 |
| geo-brand-mentions | 品牌提及扫描 | 是 geo-ai-visibility 的子集 |
| geo-platform-optimizer | 平台特定优化建议 | 是 geo-platform-analysis 的子集 |
| geo-schema | Schema 操作 | 与 geo-schema agent 重叠 |
| geo-technical | 技术 SEO | 与 geo-technical agent 重叠 |
| geo-content | 内容质量 | 与 geo-content agent 重叠 |
| geo-report | 报告生成 | 输出格式化 |

---

## 2. 各 Skill 之间的依赖关系

### 2.1 顶层依赖图

```
                    ┌─────────────────────────────────────────┐
                    │           User Request                    │
                    └──────────────────┬──────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                    ┌────▼────┐               ┌─────▼─────┐
                    │   seo   │               │   geo     │
                    │(skills/ │               │ (skills/  │
                    │  seo/)  │               │   geo/)   │
                    └────┬────┘               └─────┬─────┘
                         │                           │
         ┌───────────────┼───────────────────────┐   │
         │               │                       │   │
    ┌────▼────┐    ┌─────▼─────┐    ┌──────▼───┐  │   │
    │seo-geo  │    │seo-technical│  │seo-local │  │   │
    │(agent)  │    │(agent)     │  │(agent)   │  │   │
    └────┬────┘    └─────┬─────┘   └──────────┘  │   │
         │               │                       │   │
    ┌────▼────────────────▼───────┐              │   │
    │   geo-* agents (共享)        │              │   │
    │  ┌─────────────────────────┐│              │   │
    │  │ geo-ai-visibility       ││              │   │
    │  │ geo-content             ││              │   │
    │  │ geo-platform-analysis  ││              │   │
    │  │ geo-schema              ││              │   │
    │  │ geo-technical           ││              │   │
    │  └─────────────────────────┘│              │   │
    └─────────────────────────────┼──────────────┘   │
                                  │                  │
                         ┌────────▼────────┐         │
                         │ geo-* sub-skills│        │
                         │ (详细实现)       │         │
                         └─────────────────┘         │
                                                       │
                                        ┌──────────────▼─────────┐
                                        │   seo-geo-analyzer     │
                                        │   (独立实现)           │
                                        └───────────────────────┘
```

### 2.2 依赖关系矩阵

| Skill/A | 依赖 | 类型 | 关系描述 |
|---------|------|------|---------|
| seo (orchestrator) | seo-geo | 委托 | 主 orchestrator 委托 GEO 分析给 seo-geo agent |
| seo (orchestrator) | seo-technical | 委托 | 主 orchestrator 委托技术 SEO 给专门 agent |
| seo (orchestrator) | seo-content | 委托 | 主 orchestrator 委托内容分析给专门 agent |
| seo (orchestrator) | seo-schema | 委托 | 主 orchestrator 委托 Schema 分析给专门 agent |
| seo-geo (agent) | geo-ai-visibility | 委托 | GEO agent 调用 ai-visibility 子能力 |
| seo-geo (agent) | geo-platform-analysis | 委托 | GEO agent 调用平台分析子能力 |
| geo (orchestrator) | geo-ai-visibility | 委托 | 主 orchestrator 直接委托给 5 个核心 agents |
| geo (orchestrator) | geo-content | 委托 | 同上 |
| geo (orchestrator) | geo-platform-analysis | 委托 | 同上 |
| geo (orchestrator) | geo-schema | 委托 | 同上 |
| geo (orchestrator) | geo-technical | 委托 | 同上 |
| geo-ai-visibility | geo-citability | 包含 | 是其子功能 |
| geo-ai-visibility | geo-crawlers | 包含 | 是其子功能 |
| geo-ai-visibility | geo-llmstxt | 包含 | 是其子功能 |
| geo-ai-visibility | geo-brand-mentions | 包含 | 是其子功能 |
| geo-platform-analysis | geo-platform-optimizer | 包含 | 是其子功能 |
| seo-technical (agent) | geo-technical | 功能重叠 | 两者都检查技术 SEO |
| seo-content (agent) | geo-content | 功能重叠 | 两者都分析 E-E-A-T |
| seo-schema (agent) | geo-schema | 功能重叠 | 两者都检查 Schema |
| seo-geo (agent) | geo-ai-visibility | 重叠 | seo-geo 和 geo-ai-visibility 功能高度重叠 |
| seo-geo (agent) | geo-platform-analysis | 重叠 | seo-geo 和 geo-platform-analysis 功能重叠 |
| seo-geo-analyzer | seo, geo | 独立 | 独立实现，不调用其他 skills |

### 2.3 关键依赖问题

```
⚠️  循环/冗余依赖:
   seo → seo-geo → (geo-ai-visibility, geo-platform-analysis)
   geo → (geo-ai-visibility, geo-platform-analysis)
   ↓
   seo-geo 与 geo 都在调用同样的 5 个核心 agents
   区别只是包装层不同
```

---

## 3. 可组合的工作流链

### 3.1 完整 GEO 审计链 (推荐)

```
用户请求: /geo audit <url>

工作流:
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1: Discovery (顺序)                                          │
│ ├── 检测业务类型 (SaaS/Local/E-commerce/Publisher/Agency)          │
│ ├── 获取 homepage HTML                                            │
│ └── 提取 sitemap.xml 或内部链接 (最多 50 页)                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2: Parallel Analysis (并行)                                  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ geo-ai-visibility│  │ geo-platform-   │  │ geo-technical   │  │
│  │                 │  │ analysis        │  │                 │  │
│  │ • Citability    │  │ • Google AIO    │  │ • Crawlability  │  │
│  │ • Crawler Access│  │ • ChatGPT       │  │ • Core Web Vitals│ │
│  │ • llms.txt      │  │ • Perplexity    │  │ • SSR vs CSR    │  │
│  │ • Brand Mentions│  │ • Gemini        │  │ • Mobile        │  │
│  │ • AI Visibility │  │ • Bing Copilot  │  │ • Security      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │ geo-content      │  │ geo-schema       │                       │
│  │                 │  │                 │                       │
│  │ • E-E-A-T       │  │ • JSON-LD       │                       │
│  │ • Readability   │  │ • Microdata     │                       │
│  │ • AI Content    │  │ • Validation    │                       │
│  │ • Topical Auth  │  │ • Generation    │                       │
│  │ • Freshness     │  │                 │                       │
│  └─────────────────┘  └─────────────────┘                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3: Synthesis (顺序)                                          │
│ ├── 收集所有 agent 报告                                           │
│ ├── 计算 GEO Score (0-100)                                        │
│ ├── 生成优先行动计划                                               │
│ └── 输出客户端报告                                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 完整 SEO 审计链 (推荐)

```
用户请求: /seo audit <url>

工作流:
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1: Discovery (顺序)                                          │
│ ├── 检测业务类型                                                   │
│ └── 爬取网站结构 (并行获取多页)                                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2: Parallel Analysis (并行, 7 个 agents)                     │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │seo-technical│ │seo-content │ │seo-schema  │ │seo-sitemap │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │seo-visual  │ │seo-performance│ │seo-geo    │ │seo-local   │     │
│  │(可选)      │ │(via GSC API)│ │(via geo-  │ │(条件触发) │     │
│  │            │ │            │ │ agents)   │ │            │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                  │
│  ┌────────────┐ ┌────────────┐                                   │
│  │seo-google  │ │seo-maps    │                                   │
│  │(条件触发)  │ │(条件触发)  │                                   │
│  └────────────┘ └────────────┘                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3: Synthesis                                                │
│ ├── 计算 SEO Health Score                                         │
│ ├── 生成统一报告                                                   │
│ └── 提供 PDF 导出选项                                               │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 内容优化工作流 (链式组合)

```
用户请求: /geo content <url> + 需要优化建议

工作流:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: geo-content 分析                                         │
│ ├── E-E-A-T 评分                                                 │
│ ├── 内容深度/可读性                                               │
│ ├── AI 内容检测                                                  │
│ └── 优先改进项                                                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: geo-schema 补充                                          │
│ ├── 检测现有 Schema                                               │
│ ├── 生成 Article + Person Schema                                 │
│ └── 添加 speakable 属性                                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: seo-image-gen (可选)                                     │
│ └── 生成 SEO 友好的图片资产                                       │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 平台特定优化工作流

```
用户请求: 优化特定平台 (如 Perplexity)

工作流:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: geo-platform-analysis                                     │
│ └── 评分 5 个平台, 识别目标平台弱项                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: geo-brand-mentions (如果 Reddit/YouTube 弱)               │
│ └── 扫描 Reddit/YouTube 品牌提及                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: geo-llmstxt (如果需要)                                   │
│ └── 生成/优化 llms.txt                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. 重叠/冗余技能识别与整合建议

### 4.1 重叠矩阵

| 技能对 | 重叠度 | 重叠内容 | 差异点 |
|-------|-------|---------|-------|
| seo-geo vs geo-ai-visibility | **90%** | AI 可见度, citability, crawler access, brand mentions | 包装层不同, seo-geo 是 seo 的子模块 |
| seo-geo vs geo-platform-analysis | **85%** | 平台特定优化 (AIO, ChatGPT, Perplexity) | seo-geo 是综合 agent, geo-platform-analysis 是专项 |
| seo-technical vs geo-technical | **80%** | 技术 SEO (crawlability, Core Web Vitals, mobile, security) | geo-technical 强调 SSR/CSR 对 AI 的影响 |
| seo-content vs geo-content | **75%** | E-E-A-T 评估, 可读性, 内容深度 | geo-content 强调 AI 引用就绪度 |
| seo-schema vs geo-schema | **70%** | Schema 检测, 验证, 生成 | geo-schema 强调 speakable 和 sameAs |
| geo (orchestrator) vs seo-geo (agent) | **60%** | 都是 GEO 分析入口 | geo 是独立 skill, seo-geo 是 seo 的子 agent |
| seo-geo-analyzer vs geo (orchestrator) | **50%** | 都是 GEO 分析 | seo-geo-analyzer 是独立实现, 不调用 geo agents |

### 4.2 冗余问题详述

#### 问题 1: geo-agents 被双重封装

```
当前状态:
┌─────────────┐      ┌─────────────┐      ┌──────────────────────────┐
│ seo (skill) │ ───▶ │ seo-geo     │ ───▶ │ (geo-ai-visibility,      │
│             │      │ (agent)     │      │  geo-platform-analysis,  │
└─────────────┘      └─────────────┘      │  geo-content,            │
                                           │  geo-schema,             │
┌─────────────┐      ┌─────────────┐      │  geo-technical)          │
│ geo (skill) │ ───▶ │ 直接调用    │ ───▶ │                          │
│             │      │ 5 个 agents │      └──────────────────────────┘
└─────────────┘      └─────────────┘
                                           问题:
                                           • seo-geo agent 和 geo orchestrator
                                             调用完全相同的 5 个核心 agents
                                           • 唯一的区别是包装层:
                                             - geo: "GEO-first, SEO-supported"
                                             - seo-geo: "GEO optimization for SEO"
```

#### 问题 2: geo-sub-skills 与 geo-agents 职责模糊

```
geo-ai-visibility (agent) 职责:
├── Citability 分析
├── AI Crawler Access 检查
├── llms.txt 分析
└── Brand Mention 扫描

geo-citability (skill) 职责: "Passage-level AI citation readiness"
geo-crawlers (skill) 职责: "AI crawler access and robots.txt"
geo-llmstxt (skill) 职责: "llms.txt standard analysis and generation"
geo-brand-mentions (skill) 职责: "Brand presence on AI-cited platforms"

问题:
• geo-citability/crawlers/llmstxt/brand-mentions 是 geo-ai-visibility 的子功能
• geo-ai-visibility 直接完成了所有这些工作
• 子 skills 的存在价值不明确 (除了被 geo-ai-visibility 调用?)
```

#### 问题 3: 三个 GEO 入口让人困惑

| 入口 | 定位 | 调用链 |
|-----|------|--------|
| `geo` (skill) | GEO-first orchestrator | 自己 → 5 个 geo-agents |
| `seo-geo` (agent) | SEO 框架内的 GEO | seo → seo-geo → geo-agents |
| `seo-geo-analyzer` | 独立中文工具 | 自己实现 12 维度分析 |

### 4.3 整合建议

#### 建议 1: 统一 GEO 入口，废除 seo-geo agent

```
整合方案:
┌─────────────────────────────────────────────────────────────────┐
│  现状                                                         │
│  ┌─────────┐    ┌─────────┐                                   │
│  │   seo   │───▶│ seo-geo │───▶ (geo-agents)                 │
│  └─────────┘    └─────────┘                                   │
│  ┌─────────┐    ┌─────────┐                                   │
│  │   geo   │───▶│ agents  │                                   │
│  └─────────┘    └─────────┘                                   │
│                                                                  │
│  建议                                                         │
│  ┌─────────┐                                                   │
│  │   seo   │───────────────────────────────▶ (所有分析 agents)  │
│  └─────────┘                              包括 geo-agents      │
│  ┌─────────┐                                                   │
│  │   geo   │───▶ (所有分析 agents)  [保留,统一入口]           │
│  └─────────┘                                                   │
│                                                                  │
│  • seo 和 geo 共享同一套 geo-agents                            │
│  • seo-geo agent 删除,seo 的 GEO 分析直接调用 geo-agents      │
│  • geo 保持为独立 GEO 入口 (品牌独立性)                        │
└─────────────────────────────────────────────────────────────────┘
```

#### 建议 2: 重组 geo-sub-skills 为独立 Tools

```
现状:
geo-ai-visibility (agent) 内部集成了所有 GEO 功能

建议:
┌─────────────────────────────────────────────────────────────────┐
│  geo-agents (保持不变,负责复杂分析)                              │
│  ├── geo-ai-visibility: 综合分析                               │
│  ├── geo-platform-analysis: 平台评分                           │
│  ├── geo-content: E-E-A-T 分析                                │
│  ├── geo-schema: Schema 操作                                   │
│  └── geo-technical: 技术 SEO                                  │
│                                                                  │
│  geo-sub-skills (重组为原子工具,被 agents 调用)                  │
│  ├── geo-citability ──→ 可被 content optimizer 调用            │
│  ├── geo-crawlers ─────→ 可被 technical checker 调用           │
│  ├── geo-llmstxt ──────→ 可被 llms.txt generator 调用          │
│  ├── geo-brand-mentions → 可被 brand tracker 调用               │
│  └── geo-platform-optimizer → 可被 platform-specific optimizer   │
│                                                                  │
│  或者:将 geo-sub-skills 完全合并入对应的 agents                 │
│  删除独立的 sub-skills,功能内化到 agents 中                     │
└─────────────────────────────────────────────────────────────────┘
```

#### 建议 3: 合并 seo-technical 和 geo-technical

```
现状:
┌──────────────────────┐    ┌──────────────────────┐
│ seo-technical        │    │ geo-technical        │
│ • Crawlability      │    │ • Crawlability       │
│ • Indexability      │    │ • SSR vs CSR (重点) │
│ • Security          │    │ • Core Web Vitals   │
│ • URL Structure     │    │ • Mobile            │
│ • Mobile            │    │ • Security          │
│ • Core Web Vitals   │    │ • URL Structure     │
│ • Structured Data  │    │ • Crawlability      │
│ • JS Rendering      │    │                     │
│ • IndexNow          │    │                     │
└──────────────────────┘    └──────────────────────┘

建议:合并为单一 geo-technical agent
┌──────────────────────────────────────────────────────────────┐
│ geo-technical (合并后)                                      │
│                                                              │
│ 核心检查 (9+2):                                              │
│ ├── Crawlability (robots.txt, sitemap)                       │
│ ├── Indexability (noindex, canonical)                        │
│ ├── Security (HTTPS, headers)                               │
│ ├── URL Structure                                           │
│ ├── Mobile Optimization                                     │
│ ├── Core Web Vitals (LCP, INP, CLS)                        │
│ ├── Structured Data (检测/验证)                             │
│ ├── JavaScript Rendering (SSR vs CSR - AI 重点)            │
│ ├── IndexNow Protocol                                       │
│ └── [新增] AI Crawler Directives (robots.txt AI 规则)      │
│                                                              │
│ 触发条件:                                                    │
│ • "/seo technical <url>" → 标准技术 SEO                    │
│ • "/geo technical <url>" → 强调 SSR/CSR 和 AI crawler      │
│ • "/geo audit <url>" → 调用此 agent,强调 AI 相关            │
└──────────────────────────────────────────────────────────────┘
```

#### 建议 4: 统一 seo 和 geo 的 Schema 分析

```
现状:
seo-schema 和 geo-schema 功能重叠 70%

建议:合并为统一 schema agent
┌──────────────────────────────────────────────────────────────┐
│ unified-schema (合并后)                                      │
│                                                              │
│ 功能:                                                        │
│ ├── 检测所有 Schema (JSON-LD, Microdata, RDFa)              │
│ ├── 验证 Schema.org 规范和 Google 需求                        │
│ ├── [SEO] 检查 rich result eligible types                    │
│ ├── [GEO] 强调 Organization + sameAs + speakable             │
│ └── 生成 JSON-LD 模板                                        │
│                                                              │
│ 调用方式:                                                    │
│ • seo schema <url> → 标准 Schema 分析                        │
│ • geo schema <url> → GEO 强调,额外检查 speakable/sameAs     │
└──────────────────────────────────────────────────────────────┘
```

#### 建议 5: 保留 seo-geo-analyzer 作为独立品牌

```
seo-geo-analyzer 保持独立的原因:
1. 中文界面,服务中文用户群体
2. 12 维度框架,不同于其他两者
3. 不调用其他 skills,完全独立实现
4. 不同的报告格式和保存路径

建议:保留为独立产品,明确其与其他 tools 的差异
```

### 4.4 整合后的理想架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          理想 SEO/GEO Skills 架构                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────────┐   │
│  │     seo      │         │     geo      │         │ seo-geo-analyzer │   │
│  │ (SEO-first)  │         │ (GEO-first)  │         │  (独立中文工具)   │   │
│  └──────┬───────┘         └──────┬───────┘         └──────────────────┘   │
│         │                        │                                          │
│         │  ┌─────────────────────┴─────────────────────┐                   │
│         │  │           共享 Geo Agents Pool             │                   │
│         │  └────────────────────────────────────────────┘                   │
│         │                        │                                          │
│         ▼                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐             │
│  │                    GEO Agents (5 个核心)                    │             │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │             │
│  │  │geo-ai-visibility│  │geo-platform-   │  │geo-content   │  │             │
│  │  │                │  │analysis        │  │              │  │             │
│  │  │• Citability   │  │• Google AIO   │  │• E-E-A-T    │  │             │
│  │  │• Crawler Access│  │• ChatGPT      │  │• Readability│  │             │
│  │  │• llms.txt     │  │• Perplexity   │  │• AI Content │  │             │
│  │  │• Brand Mention│  │• Gemini       │  │• Freshness  │  │             │
│  │  │                │  │• Bing Copilot│  │              │  │             │
│  │  └────────────────┘  └────────────────┘  └──────────────┘  │             │
│  │  ┌────────────────┐  ┌────────────────┐                   │             │
│  │  │geo-schema      │  │geo-technical   │                   │             │
│  │  │                │  │(已合并 seo-tech)│                   │             │
│  │  │• JSON-LD      │  │• Crawlability  │                   │             │
│  │  │• Validation   │  │• Core Web Vitals│                   │             │
│  │  │• sameAs       │  │• SSR vs CSR   │                   │             │
│  │  │• speakable    │  │• AI Crawlers │                   │             │
│  │  └────────────────┘  └────────────────┘                   │             │
│  └─────────────────────────────────────────────────────────────┘             │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────┐             │
│  │              SEO Agents (独立,非 GEO)                       │             │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │             │
│  │  │seo-local │ │seo-maps  │ │seo-google │ │seo-images │     │             │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │             │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │             │
│  │  │seo-sitemap│ │seo-visual│ │seo-plan  │                 │             │
│  │  └──────────┘ └──────────┘ └──────────┘                 │             │
│  └─────────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

整合要点:
1. seo-geo agent 删除,seo 直接调用 geo-agents
2. geo-technical 和 seo-technical 合并
3. geo-sub-skills 内化到 agents 或转为原子工具
4. seo 和 geo 共享同一套 geo-agents
5. seo-geo-analyzer 保持独立
```

---

## 5. 附录

### 5.1 触发关键词汇总

| Skill | 主要触发词 |
|-------|-----------|
| seo | "seo", "audit", "sitemap", "E-E-A-T", "AI Overviews", "technical SEO" |
| geo | "geo", "AI search", "citability", "llms.txt", "brand mentions", "GEO report" |
| seo-geo-analyzer | "分析 SEO", "GEO分析", "12维度" |
| geo-ai-visibility | (由 geo/seo 调用, 不直接触发) |
| geo-content | (由 geo/seo 调用, 不直接触发) |
| geo-platform-analysis | (由 geo/seo 调用, 不直接触发) |
| geo-schema | (由 geo/seo 调用, 不直接触发) |
| geo-technical | (由 geo/seo 调用, 不直接触发) |

### 5.2 评分体系对比

| 维度 | seo (权重) | geo (权重) |
|------|-----------|-----------|
| Technical SEO | 22% | 15% |
| Content Quality | 23% | 20% |
| On-Page SEO | 20% | - |
| Schema/Structured Data | 10% | 10% |
| Performance (CWV) | 10% | - |
| **AI Search Readiness** | 10% | **25%** (AI Citability) |
| Images | 5% | - |
| Brand Authority | - | 20% (Brand Mentions) |
| Platform Optimization | - | 10% |
| **AI Visibility** | - | **25%** (包含在 Brand Authority 中?) |

### 5.3 核心发现总结

1. **双重封装**: seo-geo agent 和 geo orchestrator 调用相同的 5 个核心 agents,造成冗余
2. **职责模糊**: geo-sub-skills 与 geo-agents 职责重叠,存在意义不明确
3. **三个入口**: seo, geo, seo-geo-analyzer 都提供类似功能,用户容易困惑
4. **技术 SEO 重叠**: seo-technical 和 geo-technical 功能重叠 80%
5. **Schema 重叠**: seo-schema 和 geo-schema 功能重叠 70%
