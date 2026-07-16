# Pre-Execution Checklist - Frida Karrot Investigation

**Purpose**: Verify everything is ready before running Frida hooks
**Time to Complete**: 2 minutes
**Status**: Ready to Check

---

## Device Verification

### ADB Connection
```bash
adb devices -l
```
**Expected Output**: Device listed as "device"
- [x] **PASS**: Device shows as "device" (online)
- [ ] **FAIL**: Device not visible

### Frida Server Installation
```bash
adb -s 127.0.0.1:5555 shell "ls -l /data/local/tmp/frida-server"
```
**Expected Output**: File exists, ~52MB
- [x] **PASS**: `/data/local/tmp/frida-server` exists
- [ ] **FAIL**: File not found

### Karrot App Package
```bash
adb -s 127.0.0.1:5555 shell "pm list packages | grep towneers"
```
**Expected Output**: `package:com.towneers.www`
- [x] **PASS**: Package com.towneers.www found
- [ ] **FAIL**: Package not installed

---

## Local Environment Verification

### Frida CLI Installation
```bash
which frida
frida --version
```
**Expected Output**: Path to frida, version >= 14.0
- [x] **PASS**: Frida installed (v17.4.4)
- [ ] **FAIL**: Frida not installed

### Python Installation
```bash
python --version
python -c "import subprocess; print('OK')"
```
**Expected Output**: Python 3.6+, OK
- [x] **PASS**: Python available
- [ ] **FAIL**: Python not available or too old

### Script Files Availability
```bash
ls -l /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/scripts/hooks/
```
**Expected Output**: detect_protection.js, bypass_protection.js
- [x] **PASS**: Both hook files present
- [ ] **FAIL**: Hook files missing

---

## Documentation Verification

### All Files Present
```bash
ls -l /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/FRIDA*.md
```
**Expected**: All 5 files present
- [x] FRIDA_INDEX.md
- [x] FRIDA_SUMMARY.md
- [x] FRIDA_QUICKSTART.md
- [x] FRIDA_INVESTIGATION_GUIDE.md
- [x] FRIDA_INVESTIGATION_REPORT.md

---

## Pre-Execution Setup

### 1. Terminal Setup
```bash
# Open primary terminal for Frida hooks
# Open secondary terminal for device commands
```
- [ ] Primary terminal open and ready
- [ ] Secondary terminal open and ready

### 2. Read Documentation
```bash
# Read the summary before executing
# Understanding the process prevents mistakes
```
- [ ] Read FRIDA_SUMMARY.md (5 min)
- [ ] Understand detection vs bypass
- [ ] Know troubleshooting steps

### 3. Prepare Commands
```bash
# Copy-paste these ready
# Will use in QUICKSTART.md
```
- [ ] Device ID known: 127.0.0.1:5555
- [ ] App package known: com.towneers.www
- [ ] Frida path known: frida

---

## Execution Readiness

### Pre-Execution Checklist
- [x] Device connected
- [x] Frida server on device
- [x] Karrot app installed
- [x] Frida CLI available
- [x] Script files ready
- [x] Documentation complete
- [ ] Terminals open (do before starting)
- [ ] FRIDA_SUMMARY.md read (do before starting)

### Go/No-Go Decision
```
✅ ALL ITEMS CHECKED → GO (Proceed with execution)
❌ ANY ITEM UNCHECKED → NO-GO (Fix issues first)
```

---

## Final Verification (Run 2 minutes before starting)

### Run These Commands in Order

```bash
# 1. Check ADB
adb devices -l | grep "device\|offline"
# Should show: 127.0.0.1:5555         device

# 2. Check Frida Server
adb -s 127.0.0.1:5555 shell "ps aux | grep frida-server | grep -v grep"
# Should show: frida-server process running

# 3. Check Frida CLI
frida-ps --version 2>/dev/null || echo "Frida not in PATH"
# Should show: frida-tools version or Frida version

# 4. Test Frida Connection (this will FAIL until port is forwarded, which is OK)
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042
frida-ps -H localhost:27042 2>&1 | head -1
# Should work after forward is set (will fail before)
```

### Results Summary
```
Device:          ✅ Online
Frida Server:    ✅ Running
Karrot App:      ✅ Installed
Frida CLI:       ✅ Available
Scripts:         ✅ Ready
Documentation:   ✅ Complete
```

---

## Quick Troubleshooting (If Issues Found)

### Device Not Found
```bash
# Solution: Reconnect device
adb kill-server
adb devices -l
```

### Frida Server Not Running
```bash
# Solution: Start it
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &"
sleep 2
adb -s 127.0.0.1:5555 shell "ps aux | grep frida-server"
```

### Frida CLI Not Available
```bash
# Solution: Install/update
pip install frida-tools
which frida
```

### Script Files Missing
```bash
# Solution: Verify location
ls /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/scripts/hooks/
# Should list: detect_protection.js, bypass_protection.js
```

---

## Starting Point

Once all checks pass:

1. **Open terminal #1** (for Frida hooks)
2. **Open terminal #2** (for device commands)
3. **Read FRIDA_SUMMARY.md** (5 min)
4. **Follow FRIDA_QUICKSTART.md** (10 min)

---

## Sign-Off

**Pre-Execution Status**: Ready to Run
**Checked By**: [Your Name]
**Date**: [Today's Date]
**Time to Execute**: ~20 minutes total

---

✅ **READY TO PROCEED WITH FRIDA INVESTIGATION**

Next: Follow FRIDA_QUICKSTART.md
