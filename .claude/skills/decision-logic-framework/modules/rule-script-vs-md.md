# Rule: Script vs Markdown Decision Logic

**Module**: `rule-script-vs-md.md`
**Version**: 1.0.0
**Category**: Decision Rules

---

## Purpose

This module defines when to use UV Python scripts (`.py`) versus single-file Markdown modules (`.md`) within a skill.

---

## Core Principle

> **Scripts are for DOING. Markdowns are for KNOWING.**

- **Scripts** (.py): Execute actions, automate tasks, call APIs, process data
- **Modules** (.md): Document patterns, define rules, provide reference, explain concepts

---

## Decision Matrix

| Criteria | Use Script (.py) | Use Module (.md) |
|----------|------------------|------------------|
| External packages needed | Yes | No |
| System commands required | Yes | No |
| API calls to external services | Yes | No |
| File I/O operations | Yes | No |
| Data processing/transformation | Yes | No |
| Reference documentation | No | Yes |
| Pattern descriptions | No | Yes |
| Rule definitions | No | Yes |
| Quick guides | No | Yes |
| Configuration examples | No | Yes |

---

## Decision Flowchart

```
┌──────────────────────────────────────────┐
│        NEW CONTENT FOR SKILL             │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│  Does it require external Python deps?   │
│  (httpx, pandas, click, psutil, etc.)    │
├──────────────────┬───────────────────────┤
│       YES        │         NO            │
│        ↓         │          ↓            │
│   UV SCRIPT      │                       │
│   (.py)          │                       │
└──────────────────┴───────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────┐
│   Does it need shell/system commands?    │
│   (subprocess, os.system, file ops)      │
├──────────────────┬───────────────────────┤
│       YES        │         NO            │
│        ↓         │          ↓            │
│   UV SCRIPT      │                       │
│   (.py)          │                       │
└──────────────────┴───────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────┐
│     Is it executable automation?         │
│     (needs to run and produce output)    │
├──────────────────┬───────────────────────┤
│       YES        │         NO            │
│        ↓         │          ↓            │
│   UV SCRIPT      │                       │
│   (.py)          │                       │
└──────────────────┴───────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────┐
│         Use MARKDOWN MODULE              │
│              (.md)                       │
└──────────────────────────────────────────┘
```

---

## Examples: When to Use Scripts

### 1. API Integration
```python
# kalshi_get-market.py - Needs httpx for HTTP calls
#!/usr/bin/env python3
# /// script
# dependencies = ["httpx", "click"]
# ///
```
**Why**: External package (`httpx`) required for API calls.

### 2. System Analysis
```python
# system_analyze-cpu.py - Needs psutil for system metrics
#!/usr/bin/env python3
# /// script
# dependencies = ["psutil", "click"]
# ///
```
**Why**: External package (`psutil`) required for CPU metrics.

### 3. File Processing
```python
# builder_generate-agent.py - Writes files to disk
#!/usr/bin/env python3
# /// script
# dependencies = ["click", "jinja2"]
# ///
```
**Why**: File I/O and template generation require execution.

---

## Examples: When to Use Modules

### 1. API Reference
```markdown
# api-endpoints.md
Documents the available API endpoints for reference.
```
**Why**: No execution needed, pure documentation.

### 2. Pattern Documentation
```markdown
# pattern-authentication.md
Describes authentication patterns and best practices.
```
**Why**: Conceptual guide, no code execution.

### 3. Rule Definitions
```markdown
# rule-naming-convention.md
Defines the mandatory naming conventions.
```
**Why**: Policy document, referenced by agents.

### 4. Quick Start Guide
```markdown
# guide-getting-started.md
Step-by-step instructions for new users.
```
**Why**: Human-readable instructions, no automation.

---

## Reverse Engineering Third-Party Apps

When reverse-engineering a third-party app or API:

| Scenario | Choice | Rationale |
|----------|--------|-----------|
| Document API endpoints | Module (.md) | Reference only |
| Create API client | Script (.py) | Needs httpx calls |
| Document auth flow | Module (.md) | Pattern documentation |
| Implement auth client | Script (.py) | Token management |
| List webhook events | Module (.md) | Static reference |
| Process webhooks | Script (.py) | Event handling |

**Rule of Thumb**: If you're DESCRIBING it, use MD. If you're DOING it, use Script.

---

## Hybrid Approach

Some skills may need BOTH scripts and modules:

```
.claude/skills/my-api-integration/
├── SKILL.md                    # Main entry
├── scripts/
│   ├── myapi_get-users.py      # Fetch users (needs httpx)
│   ├── myapi_create-post.py    # Create post (needs httpx)
│   └── myapi_webhook-handler.py # Process webhooks
└── modules/
    ├── api-endpoints.md        # API reference
    ├── pattern-auth.md         # Auth flow docs
    └── guide-setup.md          # Setup instructions
```

---

## Anti-Patterns

### DON'T: Script for Documentation
```python
# BAD: Using script just to print docs
def main():
    print("API Endpoints: /users, /posts...")
```
**Why Bad**: Should be a markdown file.

### DON'T: Markdown for Automation
```markdown
# BAD: Instructions that should be a script
Run these commands manually:
1. curl https://api.example.com/users
2. Parse the JSON response
3. ...
```
**Why Bad**: Repetitive manual steps should be automated.

---

## Quick Decision Checklist

Before creating a new file, ask:

- [ ] Does it need external packages? → Script
- [ ] Does it need shell commands? → Script
- [ ] Does it call external APIs? → Script
- [ ] Does it process/transform data? → Script
- [ ] Is it purely documentation? → Module
- [ ] Is it a pattern/best practice? → Module
- [ ] Is it a rule/policy? → Module
- [ ] Is it a quick reference? → Module

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
