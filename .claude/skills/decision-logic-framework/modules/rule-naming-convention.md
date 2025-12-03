# Rule: Naming Convention (Mandatory Prefixes)

**Module**: `rule-naming-convention.md`
**Version**: 1.0.0
**Category**: Mandatory Rules

---

## Purpose

This module defines the **mandatory** naming conventions for all files in skills. No single-word names allowed.

---

## Core Principle

> **Every file must have a prefix that categorizes its purpose.**

This eliminates ambiguity and makes file purpose immediately clear.

---

## Script Naming (.py)

### Pattern
```
{skill-name}_{action}.py
```

### Rules
| Rule | Requirement |
|------|-------------|
| Separator | Underscore (`_`) |
| Prefix | Skill name (kebab-case) |
| Action | Verb-noun or noun (hyphen-separated) |
| Extension | `.py` |
| Min Words | 2 (prefix + action) |

### Examples

**Good Names**:
```
kalshi_get-market.py         # Skill: kalshi, Action: get-market
kalshi_search-events.py      # Skill: kalshi, Action: search-events
system_analyze-cpu.py        # Skill: system, Action: analyze-cpu
system_check-memory.py       # Skill: system, Action: check-memory
builder_generate-agent.py    # Skill: builder, Action: generate-agent
builder_validate-skill.py    # Skill: builder, Action: validate-skill
notion_create-page.py        # Skill: notion, Action: create-page
figma_export-assets.py       # Skill: figma, Action: export-assets
```

**Bad Names** (REJECTED):
```
markets.py           # NO: Single word, no prefix
get_data.py          # NO: Too generic, unclear skill
cpu.py               # NO: Single word, no action
kalshi.py            # NO: Single word, no action
analyze.py           # NO: Single word, no prefix
```

### Action Naming Patterns

| Pattern | Use Case | Examples |
|---------|----------|----------|
| `get-{noun}` | Fetch single item | `get-market`, `get-user` |
| `list-{noun}s` | Fetch collection | `list-markets`, `list-users` |
| `search-{noun}s` | Query with filters | `search-events`, `search-posts` |
| `create-{noun}` | Create new item | `create-page`, `create-agent` |
| `update-{noun}` | Modify existing | `update-config`, `update-status` |
| `delete-{noun}` | Remove item | `delete-cache`, `delete-session` |
| `analyze-{noun}` | Inspect/report | `analyze-cpu`, `analyze-deps` |
| `validate-{noun}` | Check correctness | `validate-skill`, `validate-config` |
| `generate-{noun}` | Create from template | `generate-agent`, `generate-skill` |
| `export-{noun}` | Output data | `export-assets`, `export-report` |

---

## Module Naming (.md)

### Pattern
```
{category}-{topic}.md
```

### Rules
| Rule | Requirement |
|------|-------------|
| Separator | Hyphen (`-`) |
| Category | From approved list |
| Topic | Descriptive noun/phrase |
| Extension | `.md` |
| Min Words | 2 (category + topic) |

### Approved Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| `api` | API documentation | `api-endpoints.md`, `api-authentication.md` |
| `pattern` | Design patterns | `pattern-error-handling.md`, `pattern-auth-flow.md` |
| `rule` | Policy/rules | `rule-naming.md`, `rule-file-size.md` |
| `guide` | How-to guides | `guide-setup.md`, `guide-migration.md` |
| `schema` | Data schemas | `schema-config.md`, `schema-response.md` |
| `example` | Code examples | `example-basic.md`, `example-advanced.md` |
| `reference` | Quick reference | `reference-commands.md`, `reference-flags.md` |

### Examples

**Good Names**:
```
api-endpoints.md              # Category: api, Topic: endpoints
api-authentication.md         # Category: api, Topic: authentication
pattern-error-handling.md     # Category: pattern, Topic: error-handling
pattern-retry-logic.md        # Category: pattern, Topic: retry-logic
rule-naming-convention.md     # Category: rule, Topic: naming-convention
rule-file-size-limits.md      # Category: rule, Topic: file-size-limits
guide-getting-started.md      # Category: guide, Topic: getting-started
guide-advanced-usage.md       # Category: guide, Topic: advanced-usage
schema-api-response.md        # Category: schema, Topic: api-response
example-basic-usage.md        # Category: example, Topic: basic-usage
```

**Bad Names** (REJECTED):
```
endpoints.md         # NO: Single word, no category
auth.md              # NO: Single word, ambiguous
README.md            # EXCEPTION: Standard file
getting-started.md   # NO: Missing category prefix
error-handling.md    # NO: Missing category prefix
```

---

## Workflow Naming

### Folder Pattern
```
{workflow-name}/
```

### File Patterns
```
WORKFLOW.toon              # Always uppercase, structure file
instructions.md            # Lowercase, overall guidance
checklist.md               # Lowercase, validation checklist
steps/step-{NN}-{action}.md # Step files with number prefix
```

### Step File Pattern
```
step-{NN}-{action}.md

Where:
- NN: Two-digit number (01, 02, 03, ...)
- action: Lowercase hyphenated action
```

### Examples

**Good Workflow Names**:
```
workflows/
├── feature-implementation/
│   ├── WORKFLOW.toon
│   ├── instructions.md
│   ├── checklist.md
│   └── steps/
│       ├── step-01-analyze.md
│       ├── step-02-implement.md
│       └── step-03-validate.md
│
├── api-integration/
│   ├── WORKFLOW.toon
│   └── steps/
│       ├── step-01-design-schema.md
│       ├── step-02-create-client.md
│       └── step-03-test-endpoints.md
```

**Bad Workflow Names** (REJECTED):
```
workflow/              # NO: Too generic
impl/                  # NO: Abbreviated
step1.md               # NO: Missing separator, no action
analyze.md             # NO: Not in steps/, no step number
```

---

## Skill Folder Naming

### Pattern
```
{domain}-{purpose}/

OR

{product-name}/
```

### Examples

**Good Skill Names**:
```
decision-logic-framework/     # Domain + purpose
moai-foundation-core/         # Product + domain + type
builder-skill-uvscript/       # Role + type + variant
kalshi-markets/               # Product + domain
macos-resource-optimizer/     # Platform + purpose
```

**Bad Skill Names** (REJECTED):
```
utils/                # NO: Too generic
helpers/              # NO: Too generic
core/                 # NO: Single word
my-skill/             # NO: Non-descriptive
```

---

## Validation Rules

### Script Validation
```python
def validate_script_name(name: str) -> bool:
    """
    Valid: {prefix}_{action}.py
    - Contains exactly one underscore
    - Prefix is not empty
    - Action is not empty
    - Ends with .py
    """
    if not name.endswith('.py'):
        return False
    base = name[:-3]  # Remove .py
    parts = base.split('_')
    if len(parts) != 2:
        return False
    prefix, action = parts
    return len(prefix) > 0 and len(action) > 0
```

### Module Validation
```python
def validate_module_name(name: str) -> bool:
    """
    Valid: {category}-{topic}.md
    - Contains at least one hyphen
    - Category is from approved list
    - Topic is not empty
    - Ends with .md
    """
    CATEGORIES = ['api', 'pattern', 'rule', 'guide', 'schema', 'example', 'reference']
    if not name.endswith('.md'):
        return False
    base = name[:-3]  # Remove .md
    parts = base.split('-', 1)
    if len(parts) < 2:
        return False
    category, topic = parts[0], parts[1]
    return category in CATEGORIES and len(topic) > 0
```

---

## Exception List

These standard files are exempt from prefix rules:

| File | Location | Purpose |
|------|----------|---------|
| `SKILL.md` | Skill root | Main skill definition |
| `README.md` | Any folder | Standard documentation |
| `CHANGELOG.md` | Skill root | Version history |
| `VERSION` | Skill root | Version number |
| `WORKFLOW.toon` | Workflow root | Workflow definition |

---

## Quick Reference Card

```
SCRIPTS (.py):
  Pattern:    {skill}_{action}.py
  Separator:  underscore (_)
  Example:    kalshi_get-market.py

MODULES (.md):
  Pattern:    {category}-{topic}.md
  Separator:  hyphen (-)
  Categories: api, pattern, rule, guide, schema, example, reference
  Example:    pattern-error-handling.md

WORKFLOWS:
  Folder:     {workflow-name}/
  Structure:  WORKFLOW.toon + instructions.md + steps/step-NN-{action}.md
  Example:    feature-implementation/step-01-analyze.md

REJECTED:
  - Single words (markets.py, auth.md)
  - No prefix (get_data.py, endpoints.md)
  - Wrong separator (kalshi-get-market.py, pattern_auth.md)
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
