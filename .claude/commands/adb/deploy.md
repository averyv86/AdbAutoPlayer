---
name: adb:deploy
description: "Deploy tested bot to production with safety checks and rollback"
argument-hint: "[staging|production|--rollback <backup-id>|--verify-only]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion, Task
model: inherit
---

## Pre-execution Context

!adb devices
!git status --porcelain
!ls -la "$CLAUDE_PROJECT_DIR"/src-tauri/Settings/
!ls -la "$CLAUDE_PROJECT_DIR"/.moai/backups/deployment/ 2>/dev/null || echo "No deployment backups"
!ls -la "$CLAUDE_PROJECT_DIR"/.moai/logs/deployment/ 2>/dev/null || echo "No deployment logs"

## Essential Files

@.moai/config/config.json
@src-tauri/Settings/ADB.toml
@src-tauri/Settings/AFKJourney.toml
@pyproject.toml

---

# ADB AutoPlayer Deployment Command

> Purpose: Production deployment workflow with backup, safety checks, rollback capabilities, and staged deployment strategy.
> Tier: Production (Deployment & Operations)
> Integration: Delegates to adb-device-manager agent for deployment orchestration, uses adb_deployment_helper.py for automation.

## Command Purpose

Execute safe production deployments of validated ADB AutoPlayer bot configurations with comprehensive backup strategies, device validation, staged rollout capabilities, and automatic rollback on failures. This command ensures zero-downtime deployments and maintains production stability through progressive deployment stages.

**Core Capabilities:**

- **Staged Deployment**: Support for staging validation before production deployment
- **Backup & Snapshot**: Automatic configuration backup with versioning and restore points
- **Device Pool Management**: Deploy to multiple devices with progress tracking and failure isolation
- **Safety Checks**: Pre-deployment validation, device health checks, and readiness verification
- **Rollback Support**: Automatic rollback on failure, manual rollback via --rollback flag
- **Deployment Monitoring**: Post-deployment verification, health checks, and performance tracking
- **Audit Trail**: Complete deployment history with logs, metrics, and change tracking

---

## Prerequisites

Before running `/adb:deploy`, ensure the following requirements are met:

1. **Tests Passed**: All tests passed via `/adb:test` (unit, integration, E2E)
2. **Bot Validated**: Bot configuration validated via `/adb:validate`
3. **Devices Configured**: Production devices configured in `ADB.toml`
4. **Staging Environment**: Staging device(s) available for pre-production testing
5. **Backup Directory**: Deployment backup directory exists (`.moai/backups/deployment/`)

---

## Usage Examples

### Example 1: Staging Deployment (Pre-Production Validation)

```bash
/adb:deploy staging
```

**Expected Behavior:**
- Deploy bot to staging environment only
- Validate configuration on staging device
- Run smoke tests to verify bot functionality
- Generate staging deployment report
- Prompt for production deployment approval

### Example 2: Production Deployment (Full Rollout)

```bash
/adb:deploy production
```

**Expected Behavior:**
- Create backup snapshot of current configuration
- Validate all production devices online and ready
- Deploy bot to production device pool sequentially
- Monitor deployment progress with real-time status
- Verify post-deployment health and performance
- Generate deployment completion report

### Example 3: Verify Deployment Readiness (Dry Run)

```bash
/adb:deploy --verify-only
```

**Expected Behavior:**
- Run all pre-deployment checks without deploying
- Validate device readiness and configuration integrity
- Check backup strategy and rollback capability
- Generate readiness report with recommendations
- Exit without making any changes

### Example 4: Rollback to Previous Version

```bash
/adb:deploy --rollback backup-20251201-213456
```

**Expected Behavior:**
- Restore configuration from specified backup snapshot
- Deploy rolled-back configuration to all devices
- Verify rollback success on each device
- Generate rollback completion report
- Update deployment history

---

## Step-by-Step Workflow

### PHASE 1: Pre-Deployment Validation (7 Steps)

#### Step 1.1: Validate Bot Readiness

**Objective:** Ensure bot configuration passed all validation and testing stages.

**Actions:**
1. Check if `/adb:test` was executed recently (within last 24 hours)
2. Verify test pass rate >= 80%
3. Check if `/adb:validate` completed successfully
4. Confirm configuration schema validation passed
5. Verify no critical issues detected in validation reports

**Success Criteria:**
- Tests executed recently and passed
- Validation completed without critical errors
- Bot configuration ready for deployment

**Error Handling:**
- If tests not run: Execute `/adb:test --all` automatically or prompt user
- If validation failed: Display specific validation errors, halt deployment
- If critical issues found: Recommend fixing issues before deployment

**Output Example:**
```
✓ Bot Readiness Verified
  • Last Test Run: 2025-12-01 21:30:45 (2 hours ago)
  • Test Pass Rate: 88.3% (53/60 tests passed)
  • Validation Status: Passed (no critical issues)
  • Configuration Integrity: Valid
  • Ready for deployment
```

---

#### Step 1.2: Review Deployment Plan

**Objective:** Present deployment strategy and request user approval.

**Actions:**
1. Load production device pool from `ADB.toml`
2. Determine deployment stages (staging → production)
3. Calculate estimated deployment time based on device count
4. Identify high-risk devices or configurations
5. Display deployment plan summary to user

**Deployment Plan Structure:**
```
Deployment Plan Summary:

Stage 1: Staging Validation
  • Staging Device: emulator-5554
  • Test Duration: ~5 minutes
  • Smoke Tests: 3 scenarios

Stage 2: Production Deployment
  • Production Devices: 3 devices
    - Device 1: R58N80ABCDE (Primary)
    - Device 2: emulator-5556 (Secondary)
    - Device 3: 192.168.1.100:5555 (Tertiary)
  • Deployment Strategy: Sequential (one at a time)
  • Estimated Time: 15-20 minutes
  • Rollback Capability: Enabled

Stage 3: Post-Deployment Verification
  • Health Check: All devices
  • Performance Monitoring: 10 minutes
  • Verification Tests: Bot startup validation
```

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Deployment plan ready. Proceed with staged deployment?",
        "header": "Deployment Plan",
        "multiSelect": false,
        "options": [
            {
                "label": "Deploy to Staging Only",
                "description": "Validate on staging device before production rollout"
            },
            {
                "label": "Full Deployment (Staging + Production)",
                "description": "Complete deployment pipeline with staging validation first"
            },
            {
                "label": "Skip Staging (Production Direct)",
                "description": "Deploy directly to production (not recommended)"
            },
            {
                "label": "Cancel Deployment",
                "description": "Review plan and deploy later"
            }
        ]
    }]
})
```

**Success Criteria:**
- Deployment plan generated successfully
- User approved deployment strategy

**Output Example:**
```
✓ Deployment Plan Approved
  • Strategy: Full Deployment (Staging + Production)
  • Total Devices: 4 (1 staging, 3 production)
  • Estimated Time: 20-25 minutes
  • Rollback: Enabled
```

---

#### Step 1.3: Create Backup Snapshots

**Objective:** Create versioned backup of current configuration before deployment.

**Actions:**
1. Generate backup identifier: `backup-<timestamp>`
2. Create backup directory: `.moai/backups/deployment/backup-<timestamp>/`
3. Copy current configuration files:
   - `src-tauri/Settings/ADB.toml`
   - `src-tauri/Settings/<Game>.toml`
   - `src-tauri/src-python/adb_auto_player/games/<game>/` (custom routines)
4. Generate backup manifest with metadata (timestamp, device list, config versions)
5. Compress backup archive for space efficiency (optional)

**Backup Manifest Structure:**
```json
{
  "backup_id": "backup-20251201-213456",
  "timestamp": "2025-12-01T21:34:56Z",
  "deployment_version": "1.5.0",
  "configuration_files": [
    "ADB.toml",
    "AFKJourney.toml",
    "custom_routines/"
  ],
  "devices": [
    {"serial": "emulator-5554", "status": "staging"},
    {"serial": "R58N80ABCDE", "status": "production"}
  ],
  "created_by": "adb:deploy command",
  "restore_tested": false
}
```

**Success Criteria:**
- Backup directory created successfully
- All configuration files copied
- Backup manifest generated
- Backup integrity verified

**Error Handling:**
- If backup directory creation fails: Check permissions, halt deployment
- If file copy fails: Retry operation, log error
- If backup incomplete: Do not proceed with deployment

**Output Example:**
```
✓ Backup Snapshot Created
  • Backup ID: backup-20251201-213456
  • Location: .moai/backups/deployment/backup-20251201-213456/
  • Files Backed Up: 12
  • Backup Size: 3.2 MB
  • Manifest: Generated and verified
```

---

#### Step 1.4: Validate Device Readiness

**Objective:** Verify all target devices are online, responsive, and ready for deployment.

**Actions:**
1. Execute `adb devices` to list connected devices
2. Match target devices with available devices
3. Check device authorization status
4. Test basic ADB command execution on each device
5. Measure device response time and stability
6. Verify sufficient device storage and resources

**Device Readiness Matrix:**

| Device Serial     | Status  | Response Time | Authorization | Storage Free | Ready |
|-------------------|---------|---------------|---------------|--------------|-------|
| emulator-5554     | Online  | 95ms          | Authorized    | 8.5 GB       | ✓     |
| R58N80ABCDE       | Online  | 120ms         | Authorized    | 12.3 GB      | ✓     |
| emulator-5556     | Online  | 110ms         | Authorized    | 5.2 GB       | ✓     |
| 192.168.1.100:5555| Offline | -             | -             | -            | ✗     |

**Success Criteria:**
- All staging devices online and ready
- Critical production devices online (allow some failures)
- Device response time < 500ms
- Devices authorized and accessible

**Error Handling:**
- If staging device offline: Halt deployment, staging validation required
- If all production devices offline: Abort deployment
- If subset of devices offline: Offer partial deployment or retry
- If authorization revoked: Prompt user to re-authorize devices

**Output Example:**
```
✓ Device Readiness Validated
  • Total Devices: 4
  • Online: 3 devices
  • Offline: 1 device (192.168.1.100:5555)
  • Ready for Deployment: 3 devices
  • Staging Device Ready: Yes
  • Production Readiness: 75% (3/4 devices)
```

---

#### Step 1.5: Validate Configuration Integrity

**Objective:** Perform final configuration schema validation before deployment.

**Actions:**
1. Parse `ADB.toml` and game-specific configuration files
2. Validate all required fields present and correctly formatted
3. Check device serials match production device pool
4. Verify game-specific settings compatible with target game version
5. Validate custom routine paths and file existence
6. Check for configuration conflicts or deprecated settings

**Success Criteria:**
- Configuration files parsed successfully
- All required fields present and valid
- No schema validation errors
- Configuration compatible with target devices

**Error Handling:**
- If configuration invalid: Display specific validation errors, halt deployment
- If deprecated settings found: Warn user, offer to update configuration
- If custom routines missing: Prompt to exclude or fix missing files

**Output Example:**
```
✓ Configuration Integrity Validated
  • Schema Validation: Passed
  • Required Fields: All present
  • Device Pool: 3 devices configured
  • Custom Routines: 5 routines found and validated
  • Compatibility: Compatible with target game v1.2.5
  • No deprecated settings detected
```

---

#### Step 1.6: Check Deployment Dependencies

**Objective:** Verify all deployment dependencies and tools are available.

**Actions:**
1. Check ADB version and availability (`adb version`)
2. Verify Python environment and dependencies
3. Check deployment helper scripts exist
4. Validate deployment log directories exist
5. Verify network connectivity for remote devices

**Success Criteria:**
- ADB version >= 1.0.40
- Python environment valid
- Deployment scripts available
- Log directories exist

**Error Handling:**
- If ADB not found: Prompt to install ADB, halt deployment
- If scripts missing: Regenerate scripts or abort
- If network connectivity issues: Warn user about remote device deployment risks

**Output Example:**
```
✓ Deployment Dependencies Verified
  • ADB Version: 1.0.41
  • Python Environment: 3.12.4
  • Deployment Scripts: Available
  • Log Directory: .moai/logs/deployment/
  • Network Connectivity: Verified
```

---

#### Step 1.7: Generate Pre-Deployment Report

**Objective:** Summarize all validation results and present final deployment confirmation.

**Actions:**
1. Compile validation results from Steps 1.1-1.6
2. Calculate deployment risk score based on validation outcomes
3. Highlight any warnings or non-critical issues
4. Generate pre-deployment report
5. Request final user confirmation before proceeding

**Pre-Deployment Report Structure:**
```
═══════════════════════════════════════════════════════════════
           ADB AutoPlayer Pre-Deployment Report
═══════════════════════════════════════════════════════════════

Deployment ID: deploy-20251201-213456
Timestamp: 2025-12-01 21:34:56
Bot Configuration: AFK Journey v1.5.0

───────────────────────────────────────────────────────────────
                    Validation Summary
───────────────────────────────────────────────────────────────

✓ Bot Readiness:            PASSED
✓ Test Coverage:            88.3% (53/60 tests)
✓ Configuration Validation: PASSED
✓ Backup Created:           backup-20251201-213456
✓ Device Readiness:         75% (3/4 devices online)
⚠ Device Availability:      1 device offline (non-critical)
✓ Configuration Integrity:  PASSED
✓ Deployment Dependencies:  PASSED

───────────────────────────────────────────────────────────────
                    Deployment Strategy
───────────────────────────────────────────────────────────────

Stage 1: Staging Validation
  • Device: emulator-5554
  • Duration: ~5 minutes
  • Tests: Smoke tests + Bot startup validation

Stage 2: Production Deployment
  • Devices: 3 devices (1 offline, will skip)
  • Strategy: Sequential deployment
  • Duration: ~15 minutes
  • Rollback: Enabled

───────────────────────────────────────────────────────────────
                    Risk Assessment
───────────────────────────────────────────────────────────────

Overall Risk: LOW

Identified Risks:
  • 1 device offline (192.168.1.100:5555) - will be skipped
  • No critical risks detected

Mitigation:
  • Backup snapshot created
  • Automatic rollback on failure
  • Staged deployment (staging → production)

───────────────────────────────────────────────────────────────
                    Final Confirmation
───────────────────────────────────────────────────────────────

Deployment ready. All validation checks passed.
Proceed with deployment?

═══════════════════════════════════════════════════════════════
```

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Pre-deployment validation complete. Proceed with deployment?",
        "header": "Final Confirmation",
        "multiSelect": false,
        "options": [
            {
                "label": "Proceed with Deployment",
                "description": "Start staged deployment (staging validation first)"
            },
            {
                "label": "Review Report",
                "description": "Review detailed pre-deployment report before proceeding"
            },
            {
                "label": "Cancel Deployment",
                "description": "Abort deployment and return to planning stage"
            }
        ]
    }]
})
```

**Success Criteria:**
- Pre-deployment report generated
- User reviewed and approved deployment

---

### PHASE 2: Staged Deployment Execution (3 Steps)

#### Step 2.1: Staging Deployment (Validation Stage)

**Objective:** Deploy bot to staging environment and validate functionality.

**Actions:**
1. Identify staging device from `ADB.toml` (first device or device marked as staging)
2. Deploy bot configuration to staging device
3. Execute smoke tests on staging device:
   - Bot startup validation
   - Configuration load test
   - Basic game interaction test
4. Monitor staging deployment for errors
5. Collect staging deployment logs

**Deployment Command Sequence:**
```bash
# Step 1: Copy configuration to staging device
adb -s emulator-5554 push src-tauri/Settings/ADB.toml /sdcard/AdbAutoPlayer/
adb -s emulator-5554 push src-tauri/Settings/AFKJourney.toml /sdcard/AdbAutoPlayer/

# Step 2: Restart bot service (if running)
adb -s emulator-5554 shell am force-stop com.adbautoplayer

# Step 3: Verify configuration deployed
adb -s emulator-5554 shell cat /sdcard/AdbAutoPlayer/ADB.toml
```

**Smoke Test Scenarios:**

| Test Scenario                | Expected Outcome              | Pass Criteria       |
|------------------------------|-------------------------------|---------------------|
| Bot startup validation       | Bot initializes successfully  | Exit code 0         |
| Configuration load test      | Config parsed without errors  | No exceptions       |
| Device communication test    | Device responds to ADB        | Response < 500ms    |

**Success Criteria:**
- Staging deployment completed successfully
- All smoke tests passed
- No errors detected in staging logs

**Error Handling:**
- If staging deployment fails: Abort entire deployment, rollback not needed (staging only)
- If smoke tests fail: Display test failure details, halt production deployment
- If staging device becomes unresponsive: Reconnect device, retry deployment once

**Output Example:**
```
✓ Staging Deployment Complete
  • Device: emulator-5554
  • Deployment Status: Success
  • Smoke Tests: 3/3 passed
  • Bot Startup: Validated
  • Configuration: Loaded successfully
  • Duration: 4m 32s
```

---

#### Step 2.2: Production Deployment (Sequential Rollout)

**Objective:** Deploy bot to production devices sequentially with progress tracking.

**Actions:**
1. Retrieve production device list (exclude staging devices)
2. Deploy to each device sequentially:
   - Deploy device 1 → Verify success → Proceed to device 2
   - Deploy device 2 → Verify success → Proceed to device 3
   - Continue until all devices deployed
3. Track deployment status for each device
4. Handle per-device failures gracefully (skip failed device, continue to next)
5. Generate deployment progress report

**Sequential Deployment Flow:**
```
Production Device 1 (R58N80ABCDE)
  ├─ Deploy configuration      → ✓ Success
  ├─ Verify deployment         → ✓ Success
  ├─ Test bot startup          → ✓ Success
  └─ Mark as deployed          → ✓ Complete

Production Device 2 (emulator-5556)
  ├─ Deploy configuration      → ✓ Success
  ├─ Verify deployment         → ✓ Success
  ├─ Test bot startup          → ✓ Success
  └─ Mark as deployed          → ✓ Complete

Production Device 3 (192.168.1.100:5555)
  ├─ Deploy configuration      → ✗ Failed (device offline)
  ├─ Mark as failed            → ⚠ Skipped
  └─ Continue to next device   → Next
```

**Deployment Progress Indicators:**
```
[Stage 2/3] Production Deployment

Device 1/3: R58N80ABCDE           ✓ Deployed (2m 15s)
Device 2/3: emulator-5556         ✓ Deployed (1m 58s)
Device 3/3: 192.168.1.100:5555    ✗ Failed (device offline)

Overall Progress: 67% (2/3 devices deployed successfully)
```

**Success Criteria:**
- At least 50% of production devices deployed successfully
- Critical devices (marked as primary) deployed successfully
- No catastrophic failures during deployment

**Error Handling:**
- If device deployment fails: Log error, skip device, continue to next device
- If majority of devices fail: Halt deployment, initiate rollback
- If critical device fails: Prompt user whether to continue or rollback

**Output Example:**
```
✓ Production Deployment Complete
  • Total Devices: 3
  • Deployed Successfully: 2 devices
  • Failed: 1 device (offline, skipped)
  • Success Rate: 67%
  • Duration: 12m 45s
  • Status: Partial Success (acceptable)
```

---

#### Step 2.3: Deployment Verification

**Objective:** Verify deployment success on all deployed devices.

**Actions:**
1. Iterate through successfully deployed devices
2. For each device, execute verification checks:
   - Verify configuration files exist on device
   - Test bot can be started without errors
   - Check bot can connect to game (if game running)
   - Validate custom routines loaded correctly
3. Collect verification results
4. Generate deployment verification report

**Verification Checks:**

| Device Serial     | Config Exists | Bot Startup | Game Connection | Custom Routines | Verified |
|-------------------|---------------|-------------|-----------------|-----------------|----------|
| emulator-5554     | ✓             | ✓           | ✓               | ✓               | ✓        |
| R58N80ABCDE       | ✓             | ✓           | ✓               | ✓               | ✓        |
| emulator-5556     | ✓             | ✓           | ⚠ Game not running | ✓            | ⚠        |

**Success Criteria:**
- Configuration files verified on all deployed devices
- Bot startup successful on all deployed devices
- At least 80% of verification checks passed

**Error Handling:**
- If verification fails on device: Mark device as "deployed but unverified"
- If critical verification fails: Trigger rollback procedure
- If game connection fails: Warn user (non-critical, game may not be running)

**Output Example:**
```
✓ Deployment Verification Complete
  • Devices Verified: 3/3
  • Configuration Files: All present
  • Bot Startup: All successful
  • Game Connection: 2/3 (1 device has game not running)
  • Custom Routines: All loaded
  • Overall Status: Deployed and Verified
```

---

### PHASE 3: Post-Deployment Monitoring (4 Steps)

#### Step 3.1: Health Check

**Objective:** Perform health checks on all deployed devices to ensure stability.

**Actions:**
1. Monitor device responsiveness for 5 minutes post-deployment
2. Check for any crashes or errors in bot logs
3. Measure device resource usage (CPU, memory)
4. Test device connectivity stability
5. Verify bot remains operational during monitoring period

**Health Check Metrics:**

| Device Serial     | Responsive | Errors | CPU Usage | Memory Usage | Stable |
|-------------------|------------|--------|-----------|--------------|--------|
| emulator-5554     | Yes        | 0      | 12%       | 245 MB       | ✓      |
| R58N80ABCDE       | Yes        | 0      | 15%       | 258 MB       | ✓      |
| emulator-5556     | Yes        | 1      | 18%       | 276 MB       | ⚠      |

**Success Criteria:**
- All devices responsive during monitoring period
- No critical errors detected in logs
- Resource usage within acceptable limits (CPU < 30%, Memory < 500 MB)

**Error Handling:**
- If device becomes unresponsive: Mark device for investigation, consider rollback
- If errors detected: Analyze error severity, minor errors acceptable
- If resource usage excessive: Warn user about potential performance issues

**Output Example:**
```
✓ Health Check Complete
  • Monitoring Duration: 5 minutes
  • Devices Monitored: 3
  • All Responsive: Yes
  • Errors Detected: 1 minor error (non-critical)
  • Resource Usage: Normal
  • Overall Health: Stable
```

---

#### Step 3.2: Performance Monitoring

**Objective:** Measure post-deployment performance metrics.

**Actions:**
1. Measure bot operation latency (time from action trigger to execution)
2. Test image recognition accuracy on deployed devices
3. Measure tap action execution time
4. Check for performance degradation compared to baseline
5. Collect performance metrics for reporting

**Performance Metrics:**

| Metric                    | Baseline | Current | Change    | Status |
|---------------------------|----------|---------|-----------|--------|
| Action Latency            | 120ms    | 125ms   | +4.2%     | ✓      |
| Image Recognition Accuracy| 92.3%    | 91.8%   | -0.5%     | ✓      |
| Tap Execution Time        | 85ms     | 88ms    | +3.5%     | ✓      |
| Overall Performance       | -        | -       | -2.1%     | ✓      |

**Success Criteria:**
- Performance degradation < 10% compared to baseline
- No critical performance issues detected
- Bot operates within acceptable latency thresholds

**Error Handling:**
- If performance degradation > 10%: Warn user, recommend investigation
- If critical performance issue: Consider rollback
- If metrics unavailable: Skip performance monitoring, mark as incomplete

**Output Example:**
```
✓ Performance Monitoring Complete
  • Monitoring Duration: 10 minutes
  • Performance Change: -2.1% (acceptable)
  • Action Latency: 125ms (within threshold)
  • Image Recognition: 91.8% (within threshold)
  • No critical performance issues detected
```

---

#### Step 3.3: Generate Deployment Report

**Objective:** Create comprehensive deployment report with all metrics and outcomes.

**Actions:**
1. Compile deployment data from all phases
2. Include device-by-device deployment status
3. Add verification results and health metrics
4. Document any failures or issues encountered
5. Generate recommendations for future deployments
6. Save report to `.moai/docs/reports/deployment-report-<timestamp>.md`

**Deployment Report Structure:**
```markdown
# ADB AutoPlayer Deployment Report

**Deployment ID:** deploy-20251201-213456
**Timestamp:** 2025-12-01 21:34:56
**Bot Configuration:** AFK Journey v1.5.0
**Deployment Strategy:** Staged (Staging → Production)

## Summary

- **Total Devices:** 4 (1 staging, 3 production)
- **Deployed Successfully:** 3 devices (75%)
- **Failed:** 1 device (device offline)
- **Overall Status:** Partial Success
- **Duration:** 22m 15s
- **Rollback Triggered:** No

## Deployment Timeline

| Stage | Start Time | End Time | Duration | Status |
|-------|------------|----------|----------|--------|
| Pre-Deployment Validation | 21:34:56 | 21:38:12 | 3m 16s | ✓ Passed |
| Staging Deployment | 21:38:15 | 21:42:47 | 4m 32s | ✓ Success |
| Production Deployment | 21:43:00 | 21:55:45 | 12m 45s | ⚠ Partial |
| Post-Deployment Monitoring | 21:56:00 | 22:11:00 | 15m 00s | ✓ Complete |

## Device Deployment Status

### Staging Devices

#### emulator-5554 (Staging)
- **Status:** ✓ Deployed and Verified
- **Deployment Time:** 4m 32s
- **Smoke Tests:** 3/3 passed
- **Health:** Stable

### Production Devices

#### R58N80ABCDE (Primary)
- **Status:** ✓ Deployed and Verified
- **Deployment Time:** 2m 15s
- **Verification:** All checks passed
- **Health:** Stable

#### emulator-5556 (Secondary)
- **Status:** ✓ Deployed and Verified
- **Deployment Time:** 1m 58s
- **Verification:** Game connection warning (game not running)
- **Health:** Stable with 1 minor error

#### 192.168.1.100:5555 (Tertiary)
- **Status:** ✗ Failed
- **Reason:** Device offline
- **Action:** Skipped, can be deployed later manually

## Verification Results

- **Configuration Files:** 3/3 devices verified
- **Bot Startup:** 3/3 devices successful
- **Game Connection:** 2/3 devices connected (1 game not running)
- **Custom Routines:** 3/3 devices loaded successfully

## Performance Metrics

- **Action Latency:** 125ms (baseline: 120ms, +4.2%)
- **Image Recognition Accuracy:** 91.8% (baseline: 92.3%, -0.5%)
- **Overall Performance Change:** -2.1% (acceptable)

## Health Check Results

- **Monitoring Duration:** 15 minutes
- **Devices Monitored:** 3
- **All Responsive:** Yes
- **Errors Detected:** 1 minor error (non-critical)
- **Resource Usage:** Normal (CPU: 12-18%, Memory: 245-276 MB)
- **Overall Health:** Stable

## Backup Information

- **Backup ID:** backup-20251201-213456
- **Backup Location:** .moai/backups/deployment/backup-20251201-213456/
- **Backup Size:** 3.2 MB
- **Files Backed Up:** 12
- **Restore Tested:** No (backup available for rollback)

## Issues Encountered

1. **Device Offline (192.168.1.100:5555)**
   - **Severity:** Medium
   - **Impact:** 1 device not deployed
   - **Resolution:** Device was skipped, can be deployed manually later
   - **Recommendation:** Check device connectivity and retry deployment

2. **Minor Error on emulator-5556**
   - **Severity:** Low
   - **Impact:** Non-critical, bot remains operational
   - **Resolution:** Error logged, monitoring continues
   - **Recommendation:** Review logs if error persists

## Recommendations

1. ✓ **Deployment Successful:** 75% device coverage achieved
2. ⚠ **Retry Offline Device:** Deploy to 192.168.1.100:5555 when online
3. ✓ **Backup Created:** Rollback available if needed
4. ✓ **Health Checks Passed:** No critical issues detected
5. ⚠ **Monitor Minor Error:** Review logs for emulator-5556 error

## Next Steps

- Monitor deployed devices for next 24 hours
- Retry deployment for offline device when available
- Review performance metrics daily
- Create deployment schedule for future updates

## Rollback Instructions

If rollback is needed:
```bash
/adb:deploy --rollback backup-20251201-213456
```

This will restore configuration from backup snapshot and deploy to all devices.

---

**Deployment Completed:** 2025-12-01 22:11:15
**Report Generated:** 2025-12-01 22:12:00
**Report Location:** .moai/docs/reports/deployment-report-20251201-213456.md
```

**Success Criteria:**
- Deployment report generated successfully
- All sections populated with data
- Recommendations actionable

**Output Example:**
```
✓ Deployment Report Generated
  • Location: .moai/docs/reports/deployment-report-20251201-213456.md
  • Size: 12.5 KB
  • Sections: 9
  • Recommendations: 5
  • Backup ID: backup-20251201-213456
```

---

#### Step 3.4: Present Results & Next Steps

**Objective:** Display deployment results to user and guide next actions.

**Actions:**
1. Display summary of deployment execution
2. Highlight any failures or warnings requiring attention
3. Show device deployment status and health metrics
4. Provide rollback instructions if needed
5. Offer next action options via AskUserQuestion

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Deployment complete. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Monitor Deployment",
                "description": "Continue monitoring deployed devices for stability"
            },
            {
                "label": "Retry Failed Devices",
                "description": "Attempt deployment on devices that failed"
            },
            {
                "label": "Review Deployment Report",
                "description": "Open detailed deployment report for analysis"
            },
            {
                "label": "Start Bot Operations",
                "description": "Begin bot automation on deployed devices"
            }
        ]
    }]
})
```

**Success Criteria:**
- Results presented clearly
- User guided to appropriate next action

**Output Example:**
```
═══════════════════════════════════════════════════════════════
          ADB AutoPlayer Deployment Complete
═══════════════════════════════════════════════════════════════

✓ Deployment Summary:
  • Total Devices: 4
  • Deployed Successfully: 3 devices (75%)
  • Failed: 1 device (offline, skipped)
  • Duration: 22m 15s
  • Status: Partial Success

✓ Verification:
  • Configuration Files: All verified
  • Bot Startup: All successful
  • Game Connection: 2/3 connected
  • Health Check: Stable

⚠ Attention Required:
  • 1 device offline (192.168.1.100:5555)
  • Retry deployment when device is available
  • 1 minor error on emulator-5556 (non-critical)

✓ Backup:
  • Backup ID: backup-20251201-213456
  • Rollback Available: Yes
  • Rollback Command: /adb:deploy --rollback backup-20251201-213456

───────────────────────────────────────────────────────────────
                       Recommendations
───────────────────────────────────────────────────────────────

1. ✓ Deployment successful on 75% of devices
2. ⚠ Retry deployment on offline device when available
3. ✓ Monitor deployed devices for next 24 hours
4. ⚠ Review minor error logs if error persists
5. ✓ Backup available for rollback if needed

Deployment Report: .moai/docs/reports/deployment-report-20251201-213456.md

═══════════════════════════════════════════════════════════════
```

---

## Rollback Procedure (Automatic or Manual)

### Automatic Rollback (On Failure)

**Trigger Conditions:**
- Majority of devices (> 50%) fail deployment
- Critical device deployment fails
- Staging validation fails catastrophically

**Automatic Rollback Actions:**
1. Halt deployment immediately
2. Identify successfully deployed devices
3. Restore configuration from backup snapshot on all deployed devices
4. Verify rollback success on each device
5. Generate rollback report

**Rollback Output:**
```
⚠ Automatic Rollback Triggered

Reason: Majority of devices failed deployment (2/4 failed)

Rollback Progress:
  Device 1/2: R58N80ABCDE      ✓ Rolled back
  Device 2/2: emulator-5556    ✓ Rolled back

✓ Rollback Complete
  • Devices Rolled Back: 2
  • Configuration Restored: backup-20251201-213456
  • All Devices Verified: Yes
  • Duration: 3m 45s
```

### Manual Rollback (User-Initiated)

**Command:**
```bash
/adb:deploy --rollback backup-20251201-213456
```

**Manual Rollback Actions:**
1. Validate backup ID exists
2. Load backup manifest
3. Deploy backup configuration to all production devices
4. Verify rollback success on each device
5. Update deployment history with rollback record
6. Generate rollback completion report

**Manual Rollback Output:**
```
✓ Manual Rollback Initiated

Backup ID: backup-20251201-213456
Target Devices: 3 production devices

Rollback Progress:
  Device 1/3: emulator-5554     ✓ Rolled back
  Device 2/3: R58N80ABCDE       ✓ Rolled back
  Device 3/3: emulator-5556     ✓ Rolled back

✓ Rollback Complete
  • Devices Rolled Back: 3
  • Configuration Restored: backup-20251201-213456
  • All Devices Verified: Yes
  • Duration: 4m 12s

Rollback Report: .moai/docs/reports/rollback-report-20251201-214500.md
```

---

## Success Criteria

Deployment is considered successful when ALL of the following conditions are met:

1. **Pre-Deployment Validation Passed**: All validation checks completed without critical errors
2. **Backup Created**: Configuration backup snapshot created successfully
3. **Staging Validation Passed**: Staging deployment and smoke tests completed successfully
4. **Production Deployment Success Rate >= 50%**: At least half of production devices deployed successfully
5. **Verification Passed**: Deployed devices verified and operational
6. **Health Checks Passed**: Post-deployment health monitoring completed without critical issues
7. **Deployment Report Generated**: Comprehensive deployment report created and saved

**Quality Gates:**

- ✓ Pre-deployment validation passed
- ✓ Backup snapshot created
- ✓ Staging deployment successful
- ✓ Production deployment >= 50% success rate
- ✓ Device verification passed
- ✓ Health checks stable
- ✓ Deployment report generated

**Warning Scenarios (Deployment completed but issues detected):**

- ⚠ Production deployment success rate between 50-75%
- ⚠ Minor errors detected during health checks (non-critical)
- ⚠ Performance degradation < 10% but notable
- ⚠ One or more devices offline and skipped

**Failure Scenarios (Rollback triggered):**

- ✗ Staging validation fails
- ✗ Production deployment success rate < 50%
- ✗ Critical device deployment fails
- ✗ Catastrophic errors during deployment
- ✗ Health checks detect critical issues

---

## Metadata

**Tier:** Production (Deployment & Operations)

**Required Tools:**
- `adb-device-manager`: Agent for device deployment orchestration
- `adb_deployment_helper.py`: Deployment automation script
- `adb_config_validator.py`: Configuration validation
- `adb`: Android Debug Bridge (version 1.0.40+)

**Integration Points:**
- Reads:
  - `.moai/config/config.json` (project configuration)
  - `src-tauri/Settings/ADB.toml` (device pool)
  - `src-tauri/Settings/<Game>.toml` (game-specific config)
  - `.moai/docs/reports/test-report-*.md` (test results)
  - `.moai/docs/reports/validation-report-*.md` (validation results)
- Writes:
  - `.moai/backups/deployment/backup-<timestamp>/` (backup snapshots)
  - `.moai/docs/reports/deployment-report-<timestamp>.md` (deployment report)
  - `.moai/logs/deployment/deploy-<timestamp>.log` (deployment logs)
  - `.moai/logs/deployment/rollback-<timestamp>.log` (rollback logs)

**Dependencies:**
- Python 3.12+ with deployment helper scripts
- ADB 1.0.40+ (for device communication)
- Connected devices (staging + production)
- Test results from `/adb:test` (prerequisite)
- Validation results from `/adb:validate` (prerequisite)

**Agent Delegation:**
- Delegates to `adb-device-manager` agent for deployment orchestration
- Agent handles device deployment, verification, and monitoring
- Command focuses on workflow coordination and user interaction

---

## Output Format

### Deployment Progress Indicators

Display real-time progress during deployment:

```
[Stage 1/3] Pre-Deployment Validation    ✓ Complete (3m 16s)
[Stage 2/3] Staged Deployment
  ├─ Staging Deployment                  ✓ Complete (4m 32s)
  ├─ Production Deployment               ⏳ Device 2/3 deploying...
  └─ Deployment Verification             ⏳ Pending
[Stage 3/3] Post-Deployment Monitoring   ⏳ Pending
```

### Device Deployment Status Table

Display device deployment status in structured format:

```
┌───────────────────────┬──────────────┬──────────┬──────────┬──────────┐
│ Device Serial         │ Type         │ Status   │ Duration │ Health   │
├───────────────────────┼──────────────┼──────────┼──────────┼──────────┤
│ emulator-5554         │ Staging      │ ✓ Success│ 4m 32s   │ Stable   │
│ R58N80ABCDE           │ Production   │ ✓ Success│ 2m 15s   │ Stable   │
│ emulator-5556         │ Production   │ ✓ Success│ 1m 58s   │ ⚠ Warning│
│ 192.168.1.100:5555    │ Production   │ ✗ Failed │ -        │ Offline  │
└───────────────────────┴──────────────┴──────────┴──────────┴──────────┘

Overall Success Rate: 75% (3/4 devices)
```

### Deployment Timeline

Present deployment timeline with milestones:

```
Deployment Timeline:

21:34:56  ──●  Pre-Deployment Validation Started
21:38:12  ──●  Validation Complete (3m 16s)
21:38:15  ──●  Staging Deployment Started
21:42:47  ──●  Staging Complete (4m 32s)
21:43:00  ──●  Production Deployment Started
21:55:45  ──●  Production Complete (12m 45s)
21:56:00  ──●  Post-Deployment Monitoring Started
22:11:00  ──●  Monitoring Complete (15m 00s)
22:11:15  ──●  Deployment Finished

Total Duration: 22m 15s
```

---

## Integration with ADB Workflow

This command integrates into the ADB AutoPlayer workflow:

**Workflow Sequence:**

1. `/adb:init` - Initialize ADB project and connect devices
2. `/adb:validate` - Validate bot configuration and game compatibility
3. `/adb:test` - Test device connectivity and bot functionality
4. `/adb:deploy` - Deploy bot to production ← YOU ARE HERE
5. `/adb:run <bot>` - Execute bot automation on deployed devices

**Next Step Recommendations:**

After successful deployment, users should:
- **Monitor Deployment:** Continue monitoring deployed devices for 24 hours
- **Start Bot Operations:** Execute `/adb:run <bot>` to begin automation
- **Retry Failed Devices:** Attempt deployment on offline devices when available
- **Review Deployment Report:** Analyze deployment metrics and performance

**Error Recovery:**

If deployment fails, users can:
- **Review Deployment Report:** Analyze failure reasons and resolution steps
- **Rollback to Previous Version:** Execute `/adb:deploy --rollback <backup-id>`
- **Fix Configuration Issues:** Address configuration errors and retry deployment
- **Check Device Connectivity:** Ensure all devices are online and accessible

---

## Execution Directive

YOU MUST NOW EXECUTE THE COMMAND FOLLOWING THE WORKFLOW DESCRIBED ABOVE.

1. **START PHASE 1**: Execute pre-deployment validation (Steps 1.1-1.7)
2. **PROCEED TO PHASE 2**: Run staged deployment with progress tracking
3. **COMPLETE PHASE 3**: Perform post-deployment monitoring and generate report
4. **DO NOT JUST DESCRIBE**: Execute actual deployment commands and parse real device output

Follow the workflow phases sequentially and provide detailed progress updates to the user.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Architecture:** ADB Domain Command (Production Tier)
**Integration:** adb-device-manager agent, deployment helper scripts, backup management
