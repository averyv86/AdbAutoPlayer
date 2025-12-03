# Conflict Resolver Module

## Purpose

Handle merge conflicts during upstream sync while preserving customizations.

## Conflict Types

### 1. Modify/Delete Conflict

**Scenario**: We modified a file, upstream deleted it.

**Resolution**: Keep our version (it's a customization).

```bash
git checkout --ours <file>
git add <file>
```

### 2. Both Modified Conflict

**Scenario**: Both we and upstream modified the same file.

**Resolution**: Depends on file protection level.

For **PROTECTED** files:
```bash
git checkout --ours <file>
git add <file>
```

For **MERGE_CAREFUL** files:
```bash
# Open file and manually merge
# Keep our custom sections, accept upstream improvements
git add <file>
```

### 3. Add/Add Conflict

**Scenario**: Both we and upstream added a file with same name.

**Resolution**: Keep ours (it's intentionally different).

```bash
git checkout --ours <file>
git add <file>
```

## Protected Files Resolution

Always keep ours for these files:

```bash
# Custom agents
git checkout --ours src/moai_adk/templates/.claude/agents/moai/builder-workflow-designer.md
git checkout --ours src/moai_adk/templates/.claude/agents/moai/builder-reverse-engineer.md

# Modified agents
git checkout --ours src/moai_adk/templates/.claude/agents/moai/builder-*.md

# Custom skills
git checkout --ours src/moai_adk/templates/.claude/skills/moai-library-toon/SKILL.md
```

## Automated Resolution

Use the sync script with `--auto-resolve` flag:

```bash
uv run .claude/skills/superdisco-moai-sync/scripts/sync_upstream.py --apply --auto-resolve
```

This will:
1. Detect conflicts
2. Auto-resolve protected files (keep ours)
3. Flag non-protected conflicts for manual review

## Manual Resolution Checklist

When manual resolution is needed:

- [ ] Identify conflict type
- [ ] Check file protection level
- [ ] If PROTECTED: keep ours
- [ ] If MERGE_CAREFUL: manually merge
- [ ] If SYNC_SAFE: accept theirs
- [ ] Test affected functionality
- [ ] Commit resolution

## Recovery

If something goes wrong:

```bash
# Abort merge
git merge --abort

# Hard reset to before merge
git reset --hard HEAD

# Restore from backup
git checkout origin/main -- <file>
```
