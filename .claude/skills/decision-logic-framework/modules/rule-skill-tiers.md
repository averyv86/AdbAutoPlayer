# Rule: Skill Tier System (1-4)

**Module**: `rule-skill-tiers.md`
**Version**: 1.0.0
**Category**: Decision Rules

---

## Purpose

This module defines the 4-tier classification system for skills based on complexity and content requirements.

---

## Tier Overview

| Tier | SKILL.md | modules/ | scripts/ | Use Case |
|------|----------|----------|----------|----------|
| **1** | Required (≤100 lines) | No | No | Quick reference, simple patterns |
| **2** | Required (≤300 lines) | Optional | No | Domain expertise, templates |
| **3** | Required (≤500 lines) | Optional | Required | Automation, API integration |
| **4** | Required (≤500 lines) | Required | Required | Full ecosystem, complex workflows |

---

## Tier 1: Simple Skills

### Characteristics
- **SKILL.md only** (no additional files)
- **≤100 lines** in SKILL.md
- Quick reference or single concept
- No automation needed

### Structure
```
.claude/skills/{skill-name}/
└── SKILL.md                # ≤100 lines, self-contained
```

### Examples
- Coding pattern reference
- Single API quick reference
- Simple rule definition
- Cheat sheet

### When to Use
```
Is the entire skill content ≤100 lines?
├─ YES → Tier 1
└─ NO  → Consider Tier 2+
```

---

## Tier 2: Standard Skills

### Characteristics
- **SKILL.md + modules/** (optional)
- **≤300 lines** in SKILL.md
- Multiple related concepts
- Documentation-focused
- No executable automation

### Structure
```
.claude/skills/{skill-name}/
├── SKILL.md                # ≤300 lines, main entry
└── modules/                # Optional: expanded docs
    ├── {category}-{topic}.md
    └── {category}-{topic}.md
```

### Examples
- API documentation skill
- Design pattern collection
- Rule framework
- Multi-topic guides

### When to Use
```
Does it need multiple reference documents?
├─ YES → Tier 2 (add modules/)
└─ NO  → Stay at Tier 1

Does it need executable automation?
├─ YES → Upgrade to Tier 3
└─ NO  → Stay at Tier 2
```

---

## Tier 3: Advanced Skills

### Characteristics
- **SKILL.md + scripts/** (required)
- **≤500 lines** in SKILL.md
- Executable automation
- API integration
- System commands
- modules/ optional

### Structure
```
.claude/skills/{skill-name}/
├── SKILL.md                # ≤500 lines
├── scripts/                # Required: UV Python scripts
│   ├── {skill}_{action}.py
│   └── {skill}_{action}.py
└── modules/                # Optional: supporting docs
    └── {category}-{topic}.md
```

### Examples
- API client skill (Kalshi, Notion, Figma)
- System monitoring skill
- Code generation skill
- Build automation skill

### When to Use
```
Does it need external Python packages?
├─ YES → Tier 3 (add scripts/)
└─ NO  → Stay at Tier 2

Does it need shell/system commands?
├─ YES → Tier 3 (add scripts/)
└─ NO  → Stay at Tier 2
```

---

## Tier 4: Enterprise Skills

### Characteristics
- **SKILL.md + scripts/ + modules/** (all required)
- **≤500 lines** in SKILL.md
- Full ecosystem with docs and automation
- Complex multi-operation skills
- May include MCP server integration

### Structure
```
.claude/skills/{skill-name}/
├── SKILL.md                # ≤500 lines
├── scripts/                # Required: multiple UV scripts
│   ├── {skill}_{action}.py
│   ├── {skill}_{action}.py
│   └── README.md
├── modules/                # Required: documentation
│   ├── api-{topic}.md
│   ├── pattern-{topic}.md
│   └── README.md
└── data/                   # Optional: static data
    └── {config}.toon
```

### Examples
- Platform integration skill (full Notion/Figma)
- System optimizer skill (macOS resource)
- Builder ecosystem skill
- Enterprise API skill

### When to Use
```
Does it have 5+ scripts AND need documentation?
├─ YES → Tier 4 (full ecosystem)
└─ NO  → Stay at Tier 3

Is it a platform integration with multiple operations?
├─ YES → Tier 4
└─ NO  → Assess based on complexity
```

---

## Tier Decision Flowchart

```
┌────────────────────────────────────────────┐
│           SKILL COMPLEXITY                  │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│    Can entire skill fit in ≤100 lines?     │
├──────────────────┬─────────────────────────┤
│       YES        │          NO             │
│        ↓         │           ↓             │
│    TIER 1        │                         │
└──────────────────┴────────────┬────────────┘
                                │
                                ▼
┌────────────────────────────────────────────┐
│       Does it need scripts (automation)?   │
├──────────────────┬─────────────────────────┤
│        NO        │          YES            │
│        ↓         │           ↓             │
│    TIER 2        │                         │
│  (SKILL.md +     │                         │
│   modules/)      │                         │
└──────────────────┴────────────┬────────────┘
                                │
                                ▼
┌────────────────────────────────────────────┐
│      Does it need 5+ scripts AND docs?     │
├──────────────────┬─────────────────────────┤
│        NO        │          YES            │
│        ↓         │           ↓             │
│    TIER 3        │       TIER 4            │
│  (SKILL.md +     │  (SKILL.md +            │
│   scripts/)      │   scripts/ +            │
│                  │   modules/)             │
└──────────────────┴─────────────────────────┘
```

---

## File Count Guidelines

| Tier | SKILL.md | Modules | Scripts | Total Files |
|------|----------|---------|---------|-------------|
| 1 | 1 | 0 | 0 | 1 |
| 2 | 1 | 1-5 | 0 | 2-6 |
| 3 | 1 | 0-3 | 1-5 | 2-9 |
| 4 | 1 | 3+ | 5+ | 9+ |

---

## Line Limit Guidelines

| File Type | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|-----------|--------|--------|--------|--------|
| SKILL.md | ≤100 | ≤300 | ≤500 | ≤500 |
| Module (.md) | N/A | ≤300 | ≤300 | ≤500 |
| Script (.py) | N/A | N/A | 200-500 | 200-500 |

---

## Migration Between Tiers

### Upgrading Tier 1 → Tier 2
1. Content exceeds 100 lines
2. Need to split into topics
3. Add `modules/` folder
4. Move topic content to module files
5. Update SKILL.md to reference modules

### Upgrading Tier 2 → Tier 3
1. Need executable automation
2. Add `scripts/` folder
3. Create UV Python scripts with prefix naming
4. Update SKILL.md with script catalog

### Upgrading Tier 3 → Tier 4
1. Script count exceeds 5
2. Documentation becomes essential
3. Ensure `modules/` folder exists
4. Add comprehensive documentation
5. Consider adding `data/` for configs

---

## Examples by Tier

### Tier 1 Example
```
.claude/skills/git-commit-patterns/
└── SKILL.md    # 80 lines - commit message conventions
```

### Tier 2 Example
```
.claude/skills/rest-api-patterns/
├── SKILL.md                    # 250 lines
└── modules/
    ├── pattern-pagination.md
    ├── pattern-error-codes.md
    └── guide-versioning.md
```

### Tier 3 Example
```
.claude/skills/kalshi-markets/
├── SKILL.md                    # 400 lines
└── scripts/
    ├── kalshi_get-market.py
    ├── kalshi_search-events.py
    └── kalshi_list-trades.py
```

### Tier 4 Example
```
.claude/skills/macos-resource-optimizer/
├── SKILL.md                    # 450 lines
├── scripts/
│   ├── system_analyze-cpu.py
│   ├── system_check-memory.py
│   ├── system_monitor-disk.py
│   ├── system_optimize-cache.py
│   └── system_report-status.py
├── modules/
│   ├── api-system-metrics.md
│   ├── pattern-optimization.md
│   └── guide-monitoring.md
└── data/
    └── shell-registry.toon
```

---

## Quick Reference

```
TIER 1 (Simple):     SKILL.md only (≤100 lines)
TIER 2 (Standard):   SKILL.md + modules/ (≤300 lines)
TIER 3 (Advanced):   SKILL.md + scripts/ (≤500 lines)
TIER 4 (Enterprise): SKILL.md + scripts/ + modules/ (full ecosystem)
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
