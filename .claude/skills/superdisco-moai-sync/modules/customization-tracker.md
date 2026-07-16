# Customization Tracker Module

## Purpose

Track all customizations made to MoAI-ADK fork to prevent upstream updates from overwriting them.

## Protected Files Registry

### Custom Agents (NEW)

Files created specifically for this workspace:

```
src/moai_adk/templates/.claude/agents/moai/builder-workflow-designer.md
src/moai_adk/templates/.claude/agents/moai/builder-reverse-engineer.md
```

### Modified Agents (TOON v4.0)

Files modified with TOON v4.0 integration:

```
src/moai_adk/templates/.claude/agents/moai/builder-workflow.md
src/moai_adk/templates/.claude/agents/moai/builder-agent.md
src/moai_adk/templates/.claude/agents/moai/builder-command.md
src/moai_adk/templates/.claude/agents/moai/builder-skill.md
```

### Custom Skills

```
src/moai_adk/templates/.claude/skills/moai-library-toon/
.claude/skills/superdisco-moai-sync/
```

### Local-Only Files (Never Sync)

```
CLAUDE.local.md
.moai/config/config.json
.claude/commands/moai/99-release.md
.moai/customizations/
.moai/scripts/
.moai/cache/
.moai/logs/
```

## Auto-Detection Rules

### Detection Criteria

1. **NEW Files**: Files not present in upstream
2. **MODIFIED Files**: Files with different content than upstream
3. **LOCAL-ONLY Files**: Files in protected directories

### Protection Levels

| Level | Action During Sync |
|-------|-------------------|
| PROTECTED | Never overwrite, always keep ours |
| MERGE_CAREFUL | Attempt merge, prefer ours on conflict |
| SYNC_SAFE | Safe to update from upstream |

## Usage

```python
# Check if file is protected
from track_changes import is_protected

if is_protected("src/moai_adk/templates/.claude/agents/moai/builder-agent.md"):
    print("Protected - will not be overwritten")
```

## Color Coding System

All agents and skills have a `color:` property in YAML frontmatter for quick visual identification in Claude Code UI:

### Color Scheme

| Color | Category | Pattern | Examples |
|-------|----------|---------|----------|
| **Red** | Official MoAI | `expert-*`, `manager-*`, `mcp-*`, `ai-*`, `moai-*` | expert-backend, manager-tdd, moai-foundation-core |
| **Yellow** | Custom Superdisco | `builder-workflow-designer`, `builder-workflow`, `expert-reverse-engineer`, `superdisco-*` | builder-workflow-designer, superdisco-moai-sync |
| **Blue** | Claude Code | Default for other agents/skills | general-purpose, explore |

### Detection Rules

**Red (Official MoAI)**:
- Agents: `expert-*`, `manager-*`, `mcp-*`, `ai-*`
- Special builders: `builder-agent`, `builder-skill`, `builder-command`
- Skills: `moai-*` prefix

**Yellow (Custom Superdisco)**:
- Custom agents: `builder-workflow-designer`, `builder-workflow`, `builder-reverse-engineer`
- Custom skills: `superdisco-*` prefix

**Blue (Default)**:
- All other agents and skills not matching above patterns

### Scripts

**add_colors.py** - Automation script for adding color properties:
```bash
# Preview color assignments
uv run .claude/skills/superdisco-moai-sync/scripts/add_colors.py --dry-run

# Apply colors to all agents and skills
uv run .claude/skills/superdisco-moai-sync/scripts/add_colors.py --apply

# Process only specific types
uv run .claude/skills/superdisco-moai-sync/scripts/add_colors.py --agents
uv run .claude/skills/superdisco-moai-sync/scripts/add_colors.py --skills
```

**Features**:
- Automatically detects agent/skill names from YAML frontmatter
- Assigns colors based on naming conventions
- Creates backups before modifying files
- Supports dry-run mode for preview
- Can process agents and skills separately

**check_agents.py** (Planned) - Meta checker for validating color consistency:
```bash
# Validate all agents have correct colors
uv run .claude/skills/superdisco-moai-sync/scripts/check_agents.py

# Check for missing color properties
uv run .claude/skills/superdisco-moai-sync/scripts/check_agents.py --missing

# Verify color accuracy based on naming rules
uv run .claude/skills/superdisco-moai-sync/scripts/check_agents.py --verify
```

**Planned features**:
- Validate all agents/skills have color property
- Check color accuracy based on naming conventions
- Report inconsistencies and suggest fixes
- Integration with CI/CD for automated validation

## Manifest Location

Customizations are tracked in:
- `.moai/customizations/MANIFEST.md` - Human-readable list
- `.moai/customizations/upstream-changelog.md` - Sync history
