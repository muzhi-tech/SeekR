---
name: seekr-master-suite
version: "1.0.0"
description: |
  SeekR - Complete SEO+GEO Autonomous Agent Suite for English independent sites.
  Includes master orchestrator and self-evolution engine.
license: CC BY-NC-SA 4.0
compatibility: "Claude Code ≥1.0"
metadata:
  author: muzhi-tech
  geo-relevance: high
  tags:
    - seo
    - geo
    - orchestrator
    - evolution
    - automation
triggers:
  - "seekr"
  - "SEO GEO"
  - "audit my site"
  - "autonomous SEO"
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

# SeekR Master Suite

This is the **SeekR** package for Openclaw — a complete SEO+GEO autonomous agent suite.

## Included Skills

### 1. seekr — Master Orchestrator
Central orchestration skill that routes requests, executes 4 workflows, and scores with SHEEP/GEM.

**Triggers:** audit my site, SEO audit, GEO, AI visibility, keyword research, write article, 优化独立站

### 2. seekr-evolve — Self-Evolution Engine
Meta-layer that monitors metrics, detects degradation, generates strategies, runs A/B tests.

**Triggers:** evolve, optimize skills, check skill health, run parity audit, trigger evolution

## SHEEP Framework

| Dim | Name | Weight |
|---|---|---|
| S | Semantic Coverage | 25% |
| H | Human Credibility | 25% |
| E1 | Evidence Structuring | 20% |
| E2 | Ecosystem Integration | 15% |
| P | Performance Monitoring | 15% |

**GEM Score** = weighted average (0-100)

## Quick Start

```
用户: 帮我审计 https://example.com

Claude: 启动SeekR全站审计...
```

## Installation

```
# Copy to Openclaw skills directory
cp -r seekr ~/.openclaw/skills/

# Verify installation
openclaw skills list
```

## File Structure

```
seekr/
├── seekr/              # Master orchestrator skill
│   └── SKILL.md
├── seekr-evolve/       # Self-evolution engine
│   └── SKILL.md
└── README.md           # This file
```
