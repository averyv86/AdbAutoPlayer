# MoAI Customizations Manifest

> **Purpose**: Track all customizations to prevent upstream updates from overwriting them
> **Last Updated**: 2025-12-01

---

## Last Upstream Sync

- **Version**: v0.30.2
- **Date**: 2025-11-30
- **Next Target**: v0.31.2

---

## Custom Agents (DO NOT OVERWRITE)

These agents have been modified or created specifically for this workspace:

### NEW (Custom Created)
- `.claude/agents/moai/builder-reverse-engineer.md` - Repository analysis & pattern extraction

### MODIFIED (TOON v2.0 Integration)
- `.claude/agents/moai/builder-workflow.md` - UV Script workflow builder (will be renamed to builder-workflow-designer)
- `.claude/agents/moai/builder-agent.md` - Agent factory with TOON
- `.claude/agents/moai/builder-command.md` - Command factory with asset discovery
- `.claude/agents/moai/builder-skill.md` - Skill factory with Tier system

---

## Custom Skills (DO NOT OVERWRITE)

### MODIFIED
- `.claude/skills/builder-skill-uvscript/` - IndieDevDan patterns integration
- `.claude/skills/moai-foundation-core/` - Extended execution rules
- `.claude/skills/moai-library-toon/` - TOON v4.0 format

### NEW (Custom Created)
- `.claude/skills/macos-resource-optimizer/` - macOS resource optimization

---

## Custom Commands (DO NOT OVERWRITE)

- `.claude/commands/moai/99-release.md` - Local release management (NOT for distribution)

---

## Configuration Files (MERGE CAREFULLY)

These files have project-specific modifications:

- `CLAUDE.md` - HEAVILY MODIFIED (Alfred execution directives, Rule 9B)
- `CLAUDE.local.md` - LOCAL ONLY (never sync)
- `.moai/config/config.json` - Project-specific settings

---

## Safe to Update (FROM UPSTREAM)

These files can be safely updated from upstream MoAI-ADK releases:

### Agents
- `.claude/agents/moai/expert-backend.md`
- `.claude/agents/moai/expert-frontend.md`
- `.claude/agents/moai/expert-database.md`
- `.claude/agents/moai/expert-devops.md`
- `.claude/agents/moai/expert-security.md`
- `.claude/agents/moai/expert-uiux.md`
- `.claude/agents/moai/expert-debug.md`
- `.claude/agents/moai/manager-project.md`
- `.claude/agents/moai/manager-spec.md`
- `.claude/agents/moai/manager-docs.md`
- `.claude/agents/moai/manager-git.md`
- `.claude/agents/moai/manager-quality.md`
- `.claude/agents/moai/manager-strategy.md`
- `.claude/agents/moai/manager-tdd.md`
- `.claude/agents/moai/manager-resource-coordinator.md`
- `.claude/agents/moai/mcp-context7.md`
- `.claude/agents/moai/mcp-figma.md`
- `.claude/agents/moai/mcp-notion.md`
- `.claude/agents/moai/mcp-playwright.md`
- `.claude/agents/moai/mcp-sequential-thinking.md`
- `.claude/agents/moai/ai-nano-banana.md`

### Skills (if no local modifications)
- `.claude/skills/moai-lang-unified/`
- `.claude/skills/moai-platform-baas/`
- `.claude/skills/moai-workflow-docs/`
- `.claude/skills/moai-workflow-project/`
- `.claude/skills/moai-workflow-testing/`
- `.claude/skills/moai-connector-*/` (most)

### Commands
- `.claude/commands/moai/0-project.md`
- `.claude/commands/moai/1-plan.md`
- `.claude/commands/moai/2-run.md`
- `.claude/commands/moai/3-sync.md`
- `.claude/commands/moai/9-feedback.md`

---

## Sync Workflow

When a new MoAI version is released:

```bash
# 1. Check current version
cat .moai/config/config.json | grep '"version"'

# 2. Update moai-adk repo
cd moai-adk && git fetch origin && git pull origin main

# 3. Run sync tool (dry run first)
uv run .moai/scripts/sync-upstream.py --preview

# 4. Apply changes
uv run .moai/scripts/sync-upstream.py --apply

# 5. Review and commit
git diff
git add -A && git commit -m "chore: sync upstream MoAI vX.Y.Z"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.30.2 | 2025-11-30 | Last sync |
| v0.31.2 | 2025-12-01 | Pending (Version Management setup) |

---

**Note**: Always update this manifest when:
1. Creating new custom agents/skills
2. Modifying existing upstream files
3. After each upstream sync
