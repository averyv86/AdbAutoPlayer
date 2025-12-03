# TOON Workflow Usage Guide - Magisk and Zygisk

**Quick Start Guide for Using TOON Workflow Definitions**
**Version**: 1.0.0
**Last Updated**: 2025-12-02

---

## Quick Reference

### File Locations
```
Magisk Installation Workflow:
  /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/
  .claude/skills/adb/adb-game-magisk-installer/adb-magisk-installer/
  workflows/magisk-installation.toon

Zygisk Verification Workflow:
  /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/
  .claude/skills/adb/adb-game-magisk/adb-magisk/
  workflows/zygisk-verification.toon
```

### Timeline
- **Magisk Installation**: 15-30 minutes (7 phases)
- **Zygisk Verification**: 2-5 minutes (5 steps)
- **Combined Workflow**: 17-35 minutes

### Risk Levels
- **Magisk Installation**: Medium (bootloop potential, but mitigated)
- **Zygisk Verification**: Low (read-only, no device modifications)

---

## Workflow 1: Magisk Full Installation

### When to Use
- First-time Magisk installation with Zygisk
- Upgrade from older Magisk version
- Clean installation after bootloader unlock
- Complete root setup workflow

### Prerequisites Checklist
Before starting, verify:
- [ ] Device is USB-connected to computer
- [ ] ADB debugging is **enabled** on device
- [ ] Bootloader is **unlocked** (CRITICAL!)
- [ ] Device has 1+ GB free storage
- [ ] You have original boot.img backup OR will create during workflow

### Step-by-Step Execution

#### Preparation Phase (Before Workflow)
```bash
# 1. Enable ADB debugging on device
Settings > Developer Options > USB Debugging = ON

# 2. Verify ADB connection
adb devices

# 3. Verify bootloader is unlocked
adb shell getprop ro.boot.bootloader
# Should show bootloader version, not error

# 4. Create manual backup as safety measure
adb shell su -c 'dd if=/dev/block/bootdevice/by-name/boot' > boot-backup.img
```

#### Workflow Execution
```bash
# Start Magisk installation workflow
# This will guide you through all 7 phases automatically

# Phase 1: Device Verification (1-2 min)
#   - Verifies device connectivity
#   - Checks ADB debugging status
#   - Confirms bootloader unlock
# Checkpoint 1: Device Connected

# Phase 2: Boot Image Backup (2-3 min)
#   - Extracts original boot.img from device
#   - Stores backup for rollback
# Checkpoint 2: Boot Image Backed Up (with rollback enabled)

# Phase 3: Flash Environment Preparation (2-3 min)
#   - Enters fastboot mode
#   - Disables boot verification
# Checkpoint 3: Environment Ready

# Phase 4: Boot Image Flashing (2-3 min) [CRITICAL]
#   - Flashes patched boot.img
#   - DO NOT DISCONNECT DEVICE DURING THIS PHASE!
# Checkpoint 4: Boot Image Flashed

# Phase 5: Boot Verification (3-5 min)
#   - Device boots and comes back online
#   - Checks for bootloops
# Checkpoint 5: Device Booted

# Phase 6: Magisk Installation (3-5 min)
#   - Installs Magisk APK
#   - Verifies root access
# Checkpoint 6: Magisk Installed

# Phase 7: Zygisk Setup (2-3 min)
#   - Enables Zygisk module
#   - Verifies hooks
```

### Handling Interruptions

#### If Workflow Interrupted at Any Phase
```bash
# Option 1: Resume from last checkpoint
/moai:2-run magisk-installation --resume-from checkpoint-4
# Replace "checkpoint-4" with your last successful checkpoint

# Option 2: Start from specific phase
/moai:2-run magisk-installation --start-from "Phase 5"

# Option 3: Manual checkpoint recovery
# Workflow will prompt you to select checkpoint
```

#### If Device Enters Bootloop
```bash
# Automatic Recovery (if enabled)
# Workflow will automatically:
#   1. Detect bootloop
#   2. Restore original boot.img
#   3. Device reboots to normal state

# Manual Recovery (if needed)
# Use fastboot mode:
adb reboot bootloader
fastboot flash boot boot-backup.img
fastboot reboot
```

#### If Flash Fails
```bash
# Workflow will offer options:
#   1. Automatic rollback to restore original boot.img
#   2. Re-download Magisk and retry
#   3. Manual intervention with fastboot

# Manual recovery command:
fastboot flash boot boot-backup.img
fastboot reboot
```

### Success Verification
At the end, verify:
- [ ] Device boots normally (no loops)
- [ ] Magisk app installed and launches
- [ ] Magisk shows device as "rooted"
- [ ] Zygisk module is enabled
- [ ] zygisk-status shows no errors

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Device not found" | Check USB cable, enable ADB debugging, restart adb: `adb kill-server && adb devices` |
| "Permission denied" | Unlock device and allow USB debugging when prompted |
| "Bootloop" | Automatic rollback triggered (check logs) |
| "Flash timeout" | Device may be unresponsive, manual check needed |
| "Magisk won't launch" | Uninstall and reinstall Magisk APK (retry Phase 6) |

### Rollback (If Needed)
```bash
# Automatic Rollback
# Triggered automatically if:
#   - Flash operation fails
#   - Device enters bootloop
#   - Boot verification fails

# Manual Rollback
fastboot flash boot boot-backup.img
fastboot reboot

# Verify restoration
adb shell su -c 'getprop ro.boot.magic'
```

---

## Workflow 2: Zygisk Verification

### When to Use
- After completing Magisk installation (auto-runs as final step)
- Troubleshoot Zygisk issues anytime
- Verify Zygisk is working before game testing
- Diagnose hook loading failures

### Two Execution Modes

#### Mode 1: Standalone Verification (Run Anytime)
```bash
# Independent verification
/moai:2-run zygisk-verification

# Use case: Check Zygisk status on existing installation
# Time: 2-5 minutes
# Risk: None (read-only verification)
```

#### Mode 2: Final Step (Auto-runs After Installation)
```bash
# Automatically triggered after magisk-installation.toon completes
# Use case: Verify installation was successful
# Time: 2-5 minutes included in total workflow time
```

### Step-by-Step Execution

#### Step 1: Magisk Installation Check (30-45 sec)
```bash
# Verification checks:
# - Magisk app visible in app drawer
# - Magisk launches without crashes
# - Root access available
# - Version 26.0+ confirmed

# If Magisk not found:
#   Action: Reinstall Magisk APK or troubleshoot root
#   User intervention required
```

#### Step 2: Zygisk Module Status (30-45 sec)
```bash
# Verification checks:
# - Zygisk module exists in Magisk modules
# - Zygisk module is toggled ON
# - Module loads without errors

# Possible outcomes:
# 1. Enabled → Proceed to Step 3
# 2. Disabled → Workflow suggests enabling
# 3. Missing → Workflow suggests installing from repository
```

#### Step 3: Hook Loading Verification (45 sec - 1 min)
```bash
# Command executed:
adb shell zygisk-status
# Or with root:
adb shell su -c 'zygisk-status'

# Verification checks:
# - Command executes successfully
# - Hooks detected in running processes
# - No critical errors reported

# If hooks failed:
#   Move to Step 4 for diagnosis
```

#### Step 4: Error Diagnosis & Recovery (1-2 min)
```bash
# If hooks failed in Step 3:

# Diagnostic commands run:
adb shell zygisk-status
adb shell dmesg | grep -i denied
adb shell ps -A | grep zygisk

# Recovery procedures (based on error type):
1. Module Conflict
   - Disable conflicting modules one-by-one
   - Reboot after each change
   - Re-run Step 3

2. Permission/SELinux Denial
   - Check SELinux policy in Magisk
   - Review denial logs
   - Re-run Step 3

3. System Incompatibility
   - Verify Android version compatibility
   - Check Zygisk version
   - May require module update

4. General Issues
   - Clear Magisk cache
   - Reinstall Zygisk module
   - Full reboot of device
```

#### Step 5: Final Status Report (30-45 sec)
```bash
# Generates report file with:
# - Verification status summary
# - All diagnostic outputs
# - Recovery actions taken
# - Recommendations

# Five possible outcomes:

1. FULLY FUNCTIONAL ✓
   - All checks passed
   - Hooks loaded successfully
   - Ready for use
   - Recommendation: Proceed to game testing

2. PARTIALLY FUNCTIONAL ⚠
   - Core functions work
   - Some modules have issues
   - Recommendation: Disable conflicting modules

3. DISABLED ❌ (but installed)
   - Zygisk module exists but OFF
   - Action: Enable module and re-run

4. NOT INSTALLED ❌
   - Zygisk not found
   - Action: Install from Magisk repository

5. NON-FUNCTIONAL ❌
   - Major issues unresolved
   - Recommendation: Major troubleshooting or reinstall
```

### Output Files Created
```
verification-report.md
  └─ Complete report with status and findings

diagnostics.log
  └─ Raw diagnostic output from all checks

recovery-actions.md
  └─ Log of recovery attempts and results

checkpoints/
  ├─ checkpoint-step-1.json
  ├─ checkpoint-step-2.json
  └─ checkpoint-step-3.json
```

### Troubleshooting Zygisk Issues

| Symptom | Diagnosis | Solution |
|---------|-----------|----------|
| "zygisk-status not found" | Command not available | Magisk not installed, reinstall Magisk |
| "Permission denied" | Root not available | Grant root access in Magisk |
| "Hooks failed to load" | Module conflict or SELinux | Run error recovery (Step 4) |
| "Module won't enable" | Compatibility issue | Check Android version, update module |
| "Partial hook load" | Some modules conflicting | Disable problematic modules one-by-one |

### Recovery Procedures

#### If Zygisk Module Won't Enable
```bash
# 1. Check compatibility
adb shell getprop ro.build.version.release  # Check Android version
adb shell zygisk-status                     # Check Zygisk status

# 2. Clear Magisk cache
# Through Magisk Manager:
Settings > Clear cache

# 3. Reinstall Zygisk module
# Through Magisk Manager:
Modules > Uninstall Zygisk > Reboot
# Then reinstall latest version

# 4. Reboot device
adb reboot
```

#### If Hooks Keep Failing to Load
```bash
# 1. Identify conflicting module
adb shell logcat | grep zygisk

# 2. Disable suspected module
# Through Magisk Manager:
Modules > Disable suspected module > Reboot

# 3. Re-verify
/moai:2-run zygisk-verification

# 4. Re-enable module if no longer conflicts
```

---

## Combined Workflow: Full Installation + Verification

### Complete Flow (17-35 minutes)
```
START
  ↓
[Magisk Installation Workflow] (15-30 min)
  ├─ Phase 1-7
  ├─ 6 checkpoints with recovery
  └─ Automatic rollback if failure
  ↓
[Zygisk Verification Workflow] (2-5 min)
  ├─ Step 1-5
  ├─ Auto-runs as final step
  └─ Final status report
  ↓
END (Success or diagnosis for next steps)
```

### Execution Command
```bash
# Combined workflow (both run in sequence)
/moai:2-run magisk-installation
# Automatically followed by:
/moai:2-run zygisk-verification
```

### Recovery Points
- **6 checkpoints** in Magisk installation
- **3 checkpoints** in Zygisk verification
- Resume capability at any checkpoint
- Rollback enabled for critical operations

---

## Decision Trees Quick Reference

### Magisk Installation Decision Tree
```
Device Check
  ├─ Found → Phase 2
  └─ Not Found → Troubleshoot USB

Backup Check
  ├─ Exists → Use existing
  └─ Missing → Create new

Flash Preparation
  ├─ Ready → Phase 4
  └─ Issues → Review and fix

Flash Result
  ├─ Success → Phase 5
  └─ Failed → Rollback

Boot Result
  ├─ Success → Phase 6
  └─ Bootloop → Rollback

Magisk Verification
  ├─ Found → Phase 7
  └─ Missing → Reinstall APK

Zygisk Status
  ├─ Enabled → Complete
  └─ Disabled → Enable
```

### Zygisk Verification Decision Tree
```
Magisk Check
  ├─ Found → Step 2
  └─ Not Found → Troubleshoot root

Zygisk Status
  ├─ Enabled → Step 3
  ├─ Disabled → Enable & Step 3
  └─ Not Installed → Install & Step 3

Hook Loading
  ├─ All Loaded → Step 5 (Success)
  ├─ Partial → Step 4 (Diagnostics)
  └─ None → Step 4 (Full Diagnostics)

Error Type (if Step 4)
  ├─ Conflict → Disable modules
  ├─ Permission → Check SELinux
  ├─ Incompatibility → Check version
  └─ Retry → Step 3

Final Status
  ├─ Fully Functional → Success
  ├─ Partially Functional → Document limitations
  ├─ Disabled → Enable and retry
  ├─ Not Installed → Install and retry
  └─ Non-Functional → Troubleshooting guide
```

---

## Error Codes and Responses

### Magisk Installation

| Code | Error | Response |
|------|-------|----------|
| MAGISK_001 | Device not found | Check USB, enable ADB, restart adb |
| MAGISK_002 | Permission denied | Unlock device, grant USB debugging |
| MAGISK_003 | Bootloader locked | Unlock bootloader before proceeding |
| MAGISK_004 | Flash timeout | Check device, verify connectivity |
| MAGISK_005 | Bootloop detected | Auto-rollback activated |
| MAGISK_006 | Flash failed | Execute rollback, retry after verification |
| MAGISK_007 | Magisk missing | Reinstall Magisk APK |

### Zygisk Verification

| Code | Error | Response |
|------|-------|----------|
| ZYGISK_001 | Magisk not found | Reinstall Magisk or troubleshoot root |
| ZYGISK_002 | Module disabled | Enable module in Magisk Manager |
| ZYGISK_003 | Module missing | Install from Magisk repository |
| ZYGISK_004 | Hooks not loaded | Run error recovery diagnostics |
| ZYGISK_005 | Command timeout | Device may be unresponsive, manual check |
| ZYGISK_006 | Permission denied | Check SELinux policy and permissions |
| ZYGISK_007 | Incompatible version | Update Zygisk module or Android version |

---

## Performance Metrics

### Magisk Installation Timing
```
Phase 1: Device Verification         1-2 min
Phase 2: Boot Image Backup           2-3 min
Phase 3: Flash Preparation           2-3 min
Phase 4: Boot Image Flashing         2-3 min
Phase 5: Boot Verification           3-5 min
Phase 6: Magisk Installation         3-5 min
Phase 7: Zygisk Setup                2-3 min
─────────────────────────────────────────
Total Minimum                        15 min
Total Maximum                        30 min
```

### Zygisk Verification Timing
```
Step 1: Magisk Check                30-45 sec
Step 2: Zygisk Status               30-45 sec
Step 3: Hook Verification          45 sec-1 min
Step 4: Error Recovery              1-2 min
Step 5: Final Report               30-45 sec
─────────────────────────────────────────
Total Minimum                         2 min
Total Maximum                         5 min
Average Execution                   3-4 min
```

---

## Safety Best Practices

### Before Starting
1. **Backup Everything**
   - Full device backup (cloud or computer)
   - Original boot.img backup
   - Custom files and settings

2. **Verify Requirements**
   - Device bootloader unlocked
   - ADB debugging enabled
   - USB cable working
   - Sufficient battery (>50%)

3. **Secure Setup**
   - No other processes using ADB
   - No antivirus interfering
   - Stable USB connection
   - Reliable power source

### During Workflow
1. **Critical Phases**
   - Phase 4 (Boot Flashing): DO NOT DISCONNECT
   - Monitor closely for 30+ seconds after flash

2. **Watch for Issues**
   - Check device screen for errors
   - Monitor ADB output for timeouts
   - Be ready to interrupt if needed

3. **Timeout Management**
   - Phase 4: 5-minute limit
   - Phase 5: 5-minute boot limit
   - Step 3: 30-second limit

### After Workflow
1. **Verify Success**
   - Device boots normally
   - Magisk responsive
   - Zygisk hooks loading

2. **Document Results**
   - Save installation reports
   - Keep backup of logs
   - Note any warnings

---

## FAQ

**Q: Is it safe to run Magisk installation?**
A: Yes, with precautions. Rollback enabled for critical operations. Original boot.img backed up before flash.

**Q: What happens if USB connection lost during flash?**
A: Workflow pauses. Reconnect device to resume from checkpoint. Device may need manual recovery if flash incomplete.

**Q: Can I resume from any checkpoint?**
A: Yes. Each of the 9 total checkpoints (6 in installation + 3 in verification) supports resuming from the next step.

**Q: How long does it actually take?**
A: 15-30 minutes for installation, 2-5 minutes for verification. Most time spent on boot verification (3-5 min) to ensure stability.

**Q: What if Magisk installation fails?**
A: Automatic rollback restores original boot.img if flash fails or bootloop detected. Manual recovery with fastboot available.

**Q: Can Zygisk verification run independently?**
A: Yes. Can run standalone anytime to check Zygisk status. Also runs automatically as final step of installation.

**Q: What does "Zygisk hooks" mean?**
A: Zygisk injects code into running processes. "Hooks" are the injection points. If not loading, Zygisk isn't active.

**Q: How do I know if Zygisk is working?**
A: Run zygisk-status command. Reports hook count and any errors. Verification workflow automates this check.

---

## Next Steps After Completion

### If All Successful ✓
1. Device is rooted with Magisk
2. Zygisk module active and working
3. Ready for game modifications
4. Can proceed to game-specific scripts

### If Issues Found ⚠
1. Review error logs in output files
2. Follow specific recovery procedure
3. Re-run verification workflow
4. Contact developer with diagnostic logs

### Recommended Actions
- [ ] Test root access with root-checking app
- [ ] Verify Zygisk with module-dependent app
- [ ] Back up working state
- [ ] Test game compatibility
- [ ] Monitor device behavior for issues

---

## Support Resources

### Documentation
- TOON Workflow Summary: `TOON_WORKFLOW_CREATION_SUMMARY.md`
- Magisk Documentation: [Magisk GitHub](https://github.com/topjohnwu/Magisk)
- Zygisk Documentation: [Magisk Zygisk](https://github.com/topjohnwu/Magisk/blob/master/docs/zygisk.md)

### Tools
- ADB: Android Debug Bridge
- Fastboot: Bootloader interface
- Magisk Manager: Official Magisk app

### Troubleshooting
- Check logs in output folder
- Review error codes above
- Search Magisk documentation
- Contact device manufacturer for bootloader issues

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Ready for Use

For detailed technical specifications, see: `TOON_WORKFLOW_CREATION_SUMMARY.md`
