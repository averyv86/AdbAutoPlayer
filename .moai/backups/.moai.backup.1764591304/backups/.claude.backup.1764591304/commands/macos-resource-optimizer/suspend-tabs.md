---
name: macos-resource-optimizer:suspend-tabs
description: "Suspend inactive browser tabs to free memory"
argument-hint: "[--browser=chrome|dia|all] [--dry-run]"
allowed-tools:
  - Bash
  - AskUserQuestion
  - TodoWrite
model: haiku
skills:
  - moai-system-macos-resource-optimizer
---

## 📋 Pre-execution Context

!git status --porcelain

## 📁 Essential Files

@.moai/config/config.json
@.claude/skills/macos-resource-optimizer/scripts/tab_suspender.py
@.claude/skills/macos-resource-optimizer/extensions/chrome-tab-suspender/README.md

# 💤 MoAI Tab Suspender: Browser Tab Suspension

> **Architecture**: Direct execution via Bash tool
> **Delegation Model**: Minimal - executes tab_suspender.py directly

## 🎯 Command Purpose

Suspend inactive browser tabs to free memory **without closing the browser**.

**실행 대상**: $ARGUMENTS

This command provides quick memory recovery by suspending inactive tabs while keeping your browser and workflow intact.

---

## 🚫 What Gets Suspended vs Protected

**NEVER Suspended** (Protected):
- ✅ Pinned tabs (user explicitly pinned)
- ✅ Active tab (currently viewing)
- ✅ Audible tabs (playing audio/video)
- ✅ Chrome system pages (`chrome://`, `chrome-extension://`)
- ✅ Already suspended tabs

**Suspended** (Safe to recover):
- 💤 Inactive tabs (not viewed recently)
- 💤 Background tabs (not currently active)
- 💤 Non-audible tabs (no audio playing)
- 💤 Large memory consumers (100+ MB)

---

## 💡 Execution Philosophy: "Direct and Fast"

`/macos-resource-optimizer:suspend-tabs` executes tab suspension directly:

```
User Command: /macos-resource-optimizer:suspend-tabs [--browser=chrome]
    ↓
Parse Arguments (browser selection)
    ↓
Step 1: Check Extension Installed
    ├─ Native Messaging manifest exists?
    └─ Test connection with extension
    ↓
Step 2: Estimate Memory Recovery
    - Count browser processes
    - Estimate tabs and memory
    ↓
Step 3: User Confirmation (AskUserQuestion - Korean)
    "탭 일시중단을 실행하시겠습니까?"
    Options: 실행/취소
    ↓
Step 4: Execute via Bash
    uv run scripts/tab_suspender.py --suspend --browser=$SELECTED_BROWSER
    ↓
Step 5: Parse TOON Result
    browser:Chrome|tabs:45|suspended:23|time:1733097600
    ↓
Step 6: Report to User (Korean)
    "✅ 탭 일시중단 완료!"
    "23/45개 탭 일시중단"
```

---

## 🚀 PHASE 1: Check Extension Installation

**Goal**: Verify Chrome extension is installed and working

### Step 1.1: Check Native Messaging Manifest

Verify Native Messaging configuration exists:

Use TodoWrite tool to track execution phases:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "in_progress", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "pending", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "pending", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "pending", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "pending", "activeForm": "Reporting results"}
    ]
})
```

**Check Manifest**:
```bash
# Check if Native Messaging manifest exists
if [ -f "$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json" ]; then
    echo "✅ Chrome extension configured"
elif [ -f "$HOME/Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json" ]; then
    echo "✅ Dia Browser extension configured"
else
    echo "❌ Extension not installed"
    # Show installation instructions
    exit 1
fi
```

### Step 1.2: Test Connection

Test Native Messaging connection:

Use Bash tool:
```bash
# Test connection to extension
uv run scripts/tab_suspender.py --test
```

**Expected Output**:
- ✅ Found Native Messaging manifest
- ✅ Manifest valid
- ✅ Extension connection successful

**If Failed**:
Show installation instructions:
```
Extension not found or not configured.

Installation:
1. cd extensions/chrome-tab-suspender
2. ./install.sh
3. Follow prompts to install extension

Documentation:
- README: extensions/chrome-tab-suspender/README.md
- Testing: extensions/chrome-tab-suspender/TESTING.md
```

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "completed", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "pending", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "pending", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "pending", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "pending", "activeForm": "Reporting results"}
    ]
})
```

---

## 🚀 PHASE 2: Estimate Memory Recovery

**Goal**: Estimate how much memory can be recovered

### Step 2.1: Count Browser Processes

Use Bash tool to count browser processes:
```bash
# Count Chrome/Dia processes
ps aux | grep -E "(Chrome|Dia)" | grep -v grep | wc -l
```

**Rough Estimation**:
- Helper processes: 1-3 per tab
- Estimated tabs: processes / 2
- Memory per tab: 50-100 MB average
- Recovery rate: 80-90% for suspended tabs

**Example**:
```
Browser processes: 60
Estimated tabs: 30
Estimated memory: 2.4 GB
Potential recovery: 1.4 GB (assuming 60% suspendable)
```

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "completed", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "completed", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "pending", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "pending", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "pending", "activeForm": "Reporting results"}
    ]
})
```

---

## 🚀 PHASE 3: User Confirmation

**Goal**: Get user approval for tab suspension

### Step 3.1: Parse Arguments

Extract browser selection from $ARGUMENTS:
```python
browser = "chrome"  # default
if "--browser=dia" in $ARGUMENTS:
    browser = "dia"
elif "--browser=all" in $ARGUMENTS:
    browser = "all"
```

### Step 3.2: Request Approval

Use AskUserQuestion tool (Korean language, no emojis):
```python
AskUserQuestion({
    "questions": [{
        "question": "브라우저 탭 일시중단을 실행하시겠습니까?",
        "header": "탭 일시중단",
        "multiSelect": false,
        "options": [
            {
                "label": "Chrome 탭 일시중단",
                "description": "Chrome 브라우저의 비활성 탭을 일시중단합니다 (예상 복구: ~1.4GB)"
            },
            {
                "label": "Dia 탭 일시중단",
                "description": "Dia Browser의 비활성 탭을 일시중단합니다"
            },
            {
                "label": "모든 브라우저 일시중단",
                "description": "Chrome과 Dia의 모든 비활성 탭을 일시중단합니다"
            },
            {
                "label": "취소",
                "description": "탭 일시중단을 실행하지 않습니다"
            }
        ]
    }]
})
```

**If User Cancels**:
```
❌ 탭 일시중단이 취소되었습니다.

브라우저 상태는 변경되지 않았습니다.
필요시 언제든 다시 실행할 수 있습니다.
```

Exit gracefully.

**If User Approves**:
Extract selected browser and proceed to Phase 4.

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "completed", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "completed", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "completed", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "in_progress", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "pending", "activeForm": "Reporting results"}
    ]
})
```

---

## 🚀 PHASE 4: Execute Tab Suspension

**Goal**: Suspend inactive tabs via Native Messaging

### Step 4.1: Dry Run Mode

If `--dry-run` in $ARGUMENTS:
```
🔍 DRY RUN 모드

실제로 탭을 일시중단하지 않습니다.
예상 결과:
- Browser: Chrome
- Estimated tabs: ~30
- Suspendable tabs: ~18 (60%)
- Memory recovery: ~1.4 GB

실제 실행하려면 --dry-run 옵션 없이 다시 실행하세요.
```

Exit gracefully.

### Step 4.2: Execute Suspension

Use Bash tool to execute tab_suspender.py:
```bash
# Execute tab suspension
uv run scripts/tab_suspender.py --suspend --browser=$SELECTED_BROWSER
```

**Expected Output** (TOON format):
```
browser:Chrome|tabs:30|suspended:18|time:1733097600
```

**Parsing**:
```python
# Parse TOON output
output_line = result.stderr.strip()
parts = output_line.split('|')

tabs_total = int([p for p in parts if p.startswith('tabs:')][0].split(':')[1])
tabs_suspended = int([p for p in parts if p.startswith('suspended:')][0].split(':')[1])
browser_name = [p for p in parts if p.startswith('browser:')][0].split(':')[1]
```

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "completed", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "completed", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "completed", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "completed", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "in_progress", "activeForm": "Reporting results"}
    ]
})
```

---

## 🚀 PHASE 5: Report Results

**Goal**: Present results to user in Korean

### Step 5.1: Format Result Report

Generate user-friendly report:

```
✅ 탭 일시중단 완료!

📊 결과:
• 브라우저: Chrome
• 전체 탭: 30개
• 일시중단: 18개 (60%)
• 예상 메모리 복구: ~1.4 GB

💡 참고사항:
- 일시중단된 탭은 클릭하면 자동으로 다시 로드됩니다
- 고정 탭, 활성 탭, 소리 나는 탭은 보호되었습니다
- 브라우저는 계속 실행 중입니다

다음 단계:
- 메모리 확인: /macos-resource-optimizer:1-analyze
- 전체 최적화: /macos-resource-optimizer:quick-optimize
```

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check extension installation", "status": "completed", "activeForm": "Checking extension"},
        {"content": "Estimate memory recovery", "status": "completed", "activeForm": "Estimating recovery"},
        {"content": "Request user confirmation", "status": "completed", "activeForm": "Requesting confirmation"},
        {"content": "Execute tab suspension", "status": "completed", "activeForm": "Executing suspension"},
        {"content": "Report results", "status": "completed", "activeForm": "Reporting results"}
    ]
})
```

---

## 📚 Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Suspend Chrome tabs | `/macos-resource-optimizer:suspend-tabs` | Suspends inactive Chrome tabs (default) |
| Suspend Dia tabs | `/macos-resource-optimizer:suspend-tabs --browser=dia` | Suspends inactive Dia Browser tabs |
| Suspend all browsers | `/macos-resource-optimizer:suspend-tabs --browser=all` | Suspends tabs in Chrome and Dia |
| Preview only | `/macos-resource-optimizer:suspend-tabs --dry-run` | Shows what would be suspended without executing |

**Version**: 1.0.0
**Last Updated**: 2025-12-01
**Architecture**: Direct Bash execution (minimal overhead)
**Performance**: < 5 seconds execution time

---

## Error Handling

### Extension Not Installed

```
❌ Chrome extension not found

Installation required:
1. cd extensions/chrome-tab-suspender
2. ./install.sh
3. Follow prompts to install extension

Documentation:
- README: extensions/chrome-tab-suspender/README.md
- Testing Guide: extensions/chrome-tab-suspender/TESTING.md

Try again after installation.
```

### Connection Timeout

```
⚠️  Connection to extension timed out

Troubleshooting:
1. Restart Chrome completely
2. Check extension is enabled at chrome://extensions/
3. Run: uv run scripts/tab_suspender.py --test
4. If test passes, try suspension again

Need help? See extensions/chrome-tab-suspender/TESTING.md
```

### No Tabs Suspended

```
✅ Tab suspension completed

📊 Result:
• Total tabs: 10
• Suspended: 0

Reason: All tabs are protected
- Pinned tabs: Not suspended
- Active tab: Not suspended
- Audible tabs: Not suspended

This is normal if all tabs are in use.
```

---

## Integration with Other Commands

### Quick Optimize

Tab suspension is automatically integrated:
```bash
/macos-resource-optimizer:quick-optimize
# Will use tab suspension if extension installed
# Falls back to browser protection if extension missing
```

### Full Optimize

Same integration as quick-optimize:
```bash
/macos-resource-optimizer:full-optimize
# Includes tab suspension in memory optimization phase
```

### Monitor

Tab suspension can be part of continuous monitoring:
```bash
/macos-resource-optimizer:3-monitor
# Triggers tab suspension when memory > 80%
```

---

## Performance Expectations

**Execution Time**: < 5 seconds
- Extension check: < 1s
- User confirmation: 2-5s (user interaction)
- Tab suspension: 1-3s (20-50 tabs)
- Result parsing: < 0.5s

**Memory Recovery**:
- Light session (10-20 tabs): 200-500 MB
- Medium session (30-50 tabs): 500-1500 MB
- Heavy session (100+ tabs): 1500-3000 MB

**Success Rate**:
- With extension installed: 95%+
- Without extension: Graceful error with instructions

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Direct and Fast" philosophy described above.**

1. Parse $ARGUMENTS for browser selection and dry-run mode
2. Execute Phase 1: Check extension installed (Bash tool)
3. Execute Phase 2: Estimate memory recovery (quick heuristic)
4. Use AskUserQuestion to request user approval (Korean, no emojis)
5. Execute Phase 4: Suspend tabs via Bash tool (uv run tab_suspender.py)
6. Parse TOON result and report to user (Korean)
7. Use TodoWrite to track progress across all 5 phases
8. Do NOT just describe what you will do. DO IT.

---

**Command Status**: ✅ Ready for Use
**Expected Success Rate**: 95%+ (with extension installed)
**User Approval**: Required (safety measure)
**Language**: Korean for all user-facing text
