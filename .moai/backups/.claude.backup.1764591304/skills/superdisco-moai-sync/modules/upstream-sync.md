# Upstream Sync Module

## Purpose

Safely merge upstream MoAI-ADK updates while preserving local customizations.

## Git Remotes Configuration

```bash
# Verify remotes
git remote -v
# origin    https://github.com/superdisco-agents/moai-adk.git (fetch/push)
# upstream  https://github.com/modu-ai/moai-adk.git (fetch/push)

# Add upstream if not present
git remote add upstream https://github.com/modu-ai/moai-adk.git
```

## Sync Workflow

### Step 1: Fetch Upstream

```bash
git fetch upstream
```

### Step 2: Create Sync Branch

```bash
git checkout -b sync/vX.Y.Z
```

### Step 3: Merge with Conflict Resolution

```bash
# Attempt merge
git merge upstream/main --no-commit

# Check for conflicts
git status

# For protected files, keep ours
git checkout --ours <protected-file>
```

### Step 4: Complete Merge

```bash
git add -A
git commit -m "chore: sync upstream MoAI vX.Y.Z (preserve superdisco customizations)"
```

### Step 5: Merge to Main

```bash
git checkout main
git merge sync/vX.Y.Z
```

### Step 6: Push to Fork

```bash
git push origin main
```

## Protected Files During Merge

When conflicts occur in protected files:

```bash
# Keep our version (customizations)
git checkout --ours src/moai_adk/templates/.claude/agents/moai/builder-*.md
git checkout --ours src/moai_adk/templates/.claude/agents/moai/expert-*.md
```

## Version Checking

```bash
# Check current version
cat .moai/config/config.json | grep '"version"'

# Check latest upstream
curl -s https://api.github.com/repos/modu-ai/moai-adk/releases/latest | jq -r '.tag_name'
```

## Automation

Use the sync script for automated workflow:

```bash
# Preview changes
uv run .claude/skills/superdisco-moai-sync/scripts/sync_upstream.py --preview

# Apply changes
uv run .claude/skills/superdisco-moai-sync/scripts/sync_upstream.py --apply
```
