# Workflow: App Navigation and Screen Management

**File**: `app-navigation.toon`
**Skill**: `adb-navigation-base`
**Version**: 1.0.0
**Category**: app-automation
**Difficulty**: beginner

---

## Purpose

This workflow provides basic navigation functionality for Android apps including launching apps, navigating back, going to home screen, accessing recent apps, and waiting for screen state changes.

Use this workflow as a foundation for multi-step app automation workflows.

---

## Prerequisites

- Device with ADB debugging enabled
- Target app installed (for launch action)
- ADB shell access
- Input system functional

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| package_name | string | "com.daangn.android.app" | App package name |
| activity | string | ".MainActivity" | Activity name (.prefix = relative) |
| action | string | "launch" | Action: launch, back, home, recent, wait_for_screen |
| timeout | integer | 30 | Timeout in seconds |

---

## Actions

### launch
Launch specified app activity
```bash
action="launch" package_name="com.daangn.android.app" activity=".MainActivity"
```

### back
Press back button and return to previous screen
```bash
action="back"
```

### home
Press home button and return to home screen
```bash
action="home"
```

### recent
Open recent applications list
```bash
action="recent"
```

### wait_for_screen
Wait for screen state change
```bash
action="wait_for_screen" timeout=30
```

---

## Example Execution

```bash
# Launch Karrot app
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-navigation-base/workflow/app-navigation.toon \
  --param device="127.0.0.1:5555" \
  --param package_name="com.daangn.android.app" \
  --param action="launch" \
  --verbose

# Navigate back
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-navigation-base/workflow/app-navigation.toon \
  --param device="emulator-5554" \
  --param action="back" \
  --verbose

# Go to home screen
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-navigation-base/workflow/app-navigation.toon \
  --param device="192.168.1.100:5555" \
  --param action="home" \
  --verbose
```

---

**Last Updated**: 2025-12-02
