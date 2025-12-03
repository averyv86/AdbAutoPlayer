# Fork Workflow Module

## Purpose

Manage Git fork operations for MoAI-ADK customizations.

## Repository Structure

```
┌─────────────────────────────────────────────────────────────┐
│              SUPERDISCO FORK WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [upstream: modu-ai/moai-adk]                              │
│         │                                                   │
│         │ git fetch upstream                               │
│         ▼                                                   │
│  [Local moai-adk/]  ◄────── git merge (selective)          │
│         │                                                   │
│         │ git push origin                                  │
│         ▼                                                   │
│  [origin: superdisco-agents/moai-adk]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Origin (Fork)

- **URL**: `https://github.com/superdisco-agents/moai-adk.git`
- **Purpose**: Store our customizations
- **Branch**: `main`
- **Push Access**: Yes

### Upstream (Official)

- **URL**: `https://github.com/modu-ai/moai-adk.git`
- **Purpose**: Official MoAI-ADK releases
- **Branch**: `main`
- **Push Access**: No (read-only)

## Common Operations

### Push Customizations

```bash
cd moai-adk
git add -A
git commit -m "feat: superdisco customization description"
git push origin main
```

### Pull from Upstream

```bash
git fetch upstream
git merge upstream/main
# Resolve conflicts if any
git push origin main
```

### Check Sync Status

```bash
# Commits ahead of upstream
git log upstream/main..HEAD --oneline

# Commits behind upstream
git log HEAD..upstream/main --oneline
```

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Primary development |
| `sync/vX.Y.Z` | Upstream sync branches |
| `feature/*` | New customizations |

## Best Practices

1. **Always commit before sync**: Ensure local changes are committed
2. **Create sync branch**: Don't sync directly on main
3. **Review conflicts**: Check every conflict before resolving
4. **Test after merge**: Verify customizations still work
5. **Push after success**: Only push when sync is verified
