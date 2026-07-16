# ADB Project Tree Hierarchy & Migration

**Version**: 1.0.0
**Status**: ✅ Production Ready

---

## Current Structure (Pre-Reorganization)

```
/skills/adb/
├── adb-automation-coordinator/     (Agent, formerly workflow-orchestrator)
├── adb-magisk-installer/           (Game)
├── adb-screen-detection/           (Foundation)
├── adb-navigation-base/            (Foundation)
├── adb-skill-generator/            (Foundation)
├── adb-uiautomator/                (Foundation)
├── moai-domain-adb/                (MoAI domain)
└── adb-builder/                    (Builder meta-generation - NEW)
```

---

## Target Structure (Post-Reorganization)

```
/skills/adb/
│
├── adb-builder/                    ← Tier 0: Meta-generation
│   ├── scripts/
│   │   ├── adb-builder-skill.py
│   │   ├── adb-builder-bot.py
│   │   ├── adb-builder-validate.py
│   │   └── adb-project-tree-reorganizer.py
│   ├── modules/
│   └── workflows/
│
├── adb-foundation/                 ← Tier 1: Foundation skills
│   ├── adb-automation-coordinator/
│   ├── adb-screen-detection/
│   ├── adb-navigation-base/
│   ├── adb-skill-generator/
│   └── adb-uiautomator/
│
├── adb-game-karrot/                ← Tier 2: Game-specific (Karrot)
│   └── adb-karrot/
│
├── adb-game-magisk/                ← Tier 2: Game-specific (Magisk)
│   ├── adb-magisk/
│   └── adb-magisk-installer/
│
├── adb-game-afk-journey/           ← Tier 2: Game-specific (AFK Journey)
│   ├── adb-game-afk-journey/       (Created via adb-builder-bot)
│
├── adb-game-guitar-girl/           ← Tier 2: Game-specific (Guitar Girl)
│   ├── adb-game-guitar-girl/       (Created via adb-builder-bot)
│
├── adb-utility/                    ← Tier 3: Utility skills
│   └── adb-bypass/
│
└── moai-domain-adb/                ← Tier 1: MoAI domain (unchanged)
```

---

## Migration Mapping

### Foundation Skills

| Current Path | Target Path | Category | Reason |
|-------------|------------|----------|--------|
| adb-automation-coordinator/ | adb-foundation/adb-automation-coordinator/ | Foundation | Core orchestration |
| adb-screen-detection/ | adb-foundation/adb-screen-detection/ | Foundation | Core detection |
| adb-navigation-base/ | adb-foundation/adb-navigation-base/ | Foundation | Base navigation |
| adb-skill-generator/ | adb-foundation/adb-skill-generator/ | Foundation | Skill generation |
| adb-uiautomator/ | adb-foundation/adb-uiautomator/ | Foundation | UI automation |

### Game Skills

| Current Path | Target Path | Game | Reason |
|-------------|------------|------|--------|
| adb-karrot/ | adb-game-karrot/adb-karrot/ | Karrot | Game-specific |
| adb-magisk/ | adb-game-magisk/adb-magisk/ | Magisk | Game-specific |
| adb-magisk-installer/ | adb-game-magisk/adb-magisk-installer/ | Magisk | Game tools |

### Utility Skills

| Current Path | Target Path | Category | Reason |
|-------------|------------|----------|--------|
| adb-bypass/ | adb-utility/adb-bypass/ | Utility | App bypassing |

### Tier 0 (Meta-generation)

| Current Path | Target Path | Purpose |
|-------------|------------|---------|
| adb-builder/ | adb-builder/ | Skill generation (unchanged) |

### Tier 1 (MoAI)

| Current Path | Target Path | Purpose |
|-------------|------------|---------|
| moai-domain-adb/ | moai-domain-adb/ | MoAI integration (unchanged) |

---

## Reference Updates

### SKILL.md Path Updates

**Before**:
```yaml
parent: /skills/adb/adb-feature
imports:
  - /skills/adb/adb-foundation
```

**After**:
```yaml
parent: /skills/adb/adb-foundation/adb-feature
imports:
  - /skills/adb/adb-foundation
```

### Command References

**Before**:
```
uv run .claude/skills/adb/adb-feature/scripts/main.py
```

**After**:
```
uv run .claude/skills/adb/adb-foundation/adb-feature/scripts/main.py
```

### Documentation Links

**Before**:
```markdown
See [adb-foundation](../adb-foundation/modules/core.md)
```

**After**:
```markdown
See [adb-foundation](../../adb-foundation/modules/core.md)
```

---

## Migration Procedure

### Phase 1: Backup

```bash
# Create timestamped backup
cp -r .claude/skills/adb .claude/backup/adb_$(date +%Y%m%d_%H%M%S)
```

### Phase 2: Create Target Directories

```bash
# Foundation tier
mkdir -p .claude/skills/adb/adb-foundation

# Game tiers
mkdir -p .claude/skills/adb/adb-game-karrot
mkdir -p .claude/skills/adb/adb-game-magisk
mkdir -p .claude/skills/adb/adb-game-afk-journey
mkdir -p .claude/skills/adb/adb-game-guitar-girl

# Utility tier
mkdir -p .claude/skills/adb/adb-utility
```

### Phase 3: Move Skills

```bash
# Foundation
mv .claude/skills/adb/adb-automation-coordinator .claude/skills/adb/adb-foundation/
mv .claude/skills/adb/adb-screen-detection .claude/skills/adb/adb-foundation/
mv .claude/skills/adb/adb-navigation-base .claude/skills/adb/adb-foundation/
mv .claude/skills/adb/adb-skill-generator .claude/skills/adb/adb-foundation/
mv .claude/skills/adb/adb-uiautomator .claude/skills/adb/adb-foundation/

# Games
mv .claude/skills/adb/adb-karrot .claude/skills/adb/adb-game-karrot/
mv .claude/skills/adb/adb-magisk .claude/skills/adb/adb-game-magisk/
mv .claude/skills/adb/adb-magisk-installer .claude/skills/adb/adb-game-magisk/

# Utility
mv .claude/skills/adb/adb-bypass .claude/skills/adb/adb-utility/
```

### Phase 4: Update References

Search and replace in all files:
- `../adb-foundation` → `../../adb-foundation`
- `/skills/adb/adb-` → `/skills/adb/adb-{tier}/adb-`

### Phase 5: Validate Migration

```bash
# Check all paths exist
find .claude/skills/adb -name "SKILL.md" | wc -l
# Should show 9+ results

# Check references work
grep -r "adb-" .claude/skills/adb --include="*.md" | head -20
```

---

## Rollback Procedure

If migration fails:

```bash
# Restore from backup
rm -rf .claude/skills/adb
cp -r .claude/backup/adb_YYYYMMDD_HHMMSS .claude/skills/adb
```

---

## Tier System Rationale

### Tier 0: Meta-Generation
- **Purpose**: Tools that create other skills
- **Examples**: adb-builder-*
- **Count**: 1
- **Update Frequency**: Low

### Tier 1: Foundation
- **Purpose**: Core infrastructure
- **Examples**: Screen detection, navigation, UI automation
- **Count**: 5
- **Update Frequency**: Medium
- **Dependency**: None

### Tier 2: Game-Specific
- **Purpose**: Game automation
- **Examples**: adb-game-karrot, adb-game-afk-journey
- **Count**: 4 games
- **Update Frequency**: High
- **Dependency**: Tier 1

### Tier 3: Utility
- **Purpose**: Support tools
- **Examples**: App bypassing, testing utilities
- **Count**: 1+
- **Update Frequency**: Low
- **Dependency**: Tier 1

---

## Benefits of New Structure

✅ **Organization**: Clear tier system
✅ **Scalability**: Easy to add new games
✅ **Maintainability**: Grouped by function
✅ **Discoverability**: Clear categorization
✅ **Reusability**: Foundation shared across games
✅ **Testing**: Easy to isolate game-specific code

---

**Status**: ✅ Production Ready
**Maturity**: 95%
