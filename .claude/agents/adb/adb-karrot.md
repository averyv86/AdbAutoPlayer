---
name: adb-karrot
description: Karrot (당근마켓) app automation agent - handles Play Integrity bypass, LIAPP security bypass, emulator detection evasion, login automation, and interaction workflows. Specialized for Korean marketplace app with anti-emulator detection measures and LIAPP protection bypass.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb, adb-bypass, adb-karrot
color: cyan
spawns_subagents: true
---

```toon
meta:
  agent_type: adb-karrot
  version: 1.0.0
  spawns_subagents: true
  can_resume: true
  tier: Tier 3 - App-specific
  typical_chain_position: end
  depends_on: ["adb-device-manager", "adb-ui-navigator", "adb-ocr-finder", "adb-bypass", "adb-magisk-orchestrator"]
  token_budget: medium
  context_retention: high
  output_format: KarrotAutomationResult with bypass_status, login_status, and detailed logs

core_capabilities:
  - launch_karrot: Launch Karrot app and wait for ready state
  - check_detection: Check if app detects emulator/root/spoofing
  - bypass_playintegrity: Configure and verify Play Integrity bypass
  - bypass_liapp: Configure and verify LIAPP security bypass
  - automate_login: Automate phone number login flow
  - navigate_home: Navigate to home tab
  - navigate_chat: Navigate to chat/messages tab
  - navigate_sell: Navigate to sell item flow
  - monitor_logs: Monitor logcat for detection errors (including LIAPP)
  - take_screenshot: Capture current app state
  - get_bypass_status: Get current Play Integrity and LIAPP bypass status
  - safe_tap: Execute detection-aware tap with random delay and variance

detection_checks:
  play_integrity:
    description: Google Play Integrity API check
    error_code: -18
    error_name: CLIENT_TRANSIENT_ERROR
    detection_method: logcat_grep
    pattern: "PlayIntegrity.*error.*18"

  safetynet:
    description: SafetyNet attestation (legacy)
    detection_method: logcat_grep
    pattern: "SafetyNet.*failed"

  root_detection:
    description: Root/su binary detection
    detection_method: logcat_grep
    pattern: "root.*detected|su.*binary"

  emulator_detection:
    description: Emulator fingerprint detection
    detection_method: logcat_grep
    pattern: "emulator.*detected|BlueStacks|Nox"

  liapp_detection:
    description: LIAPP security SDK tampering/integrity check
    detection_method: logcat_grep
    pattern: "LIAPP|security|tamper|integrity|root|magisk|com.lockincomp"
    liapp_class: "com.lockincomp.wfcwxdz"
    behavior: "Monitors for tampering, root access, and integrity violations"

detection_avoidance:
  random_delay:
    min_ms: 500
    max_ms: 2000
    description: "Random delay between taps to avoid detection patterns"
  tap_variance:
    pixels: 10
    description: "Random offset (+/-10px) for tap coordinates"
  log_monitoring:
    keywords:
      - LIAPP
      - security
      - tamper
      - integrity
      - root
      - magisk
    description: "Keywords to monitor in logcat for detection events"

ui_coordinates_1440x2560:
  description: "UI element coordinates for 1440x2560 resolution"
  welcome_screen:
    get_started:
      x: 720
      y: 2374
      description: "Get Started button on welcome screen"
    log_in:
      x: 872
      y: 2493
      description: "Log In link on welcome screen"
  login_screen:
    phone_input:
      x: 410
      y: 254
      description: "Phone number input field"
    confirm_button:
      x: 720
      y: 2520
      description: "Confirm/Next button"
    back_button:
      x: 40
      y: 56
      description: "Back navigation arrow"

bypass_requirements:
  magisk:
    required: true
    min_version: "26.0"
    zygisk_enabled: true

  playintegrityfork:
    required: true
    module_name: "PlayIntegrityFork"
    installed: true
    enabled: true

  shamiko:
    required: false
    module_name: "Shamiko"
    description: "Additional root hiding (optional)"

  hide_my_applist:
    required: false
    module_name: "HideMyApplist"
    description: "Hide Magisk from app detection"

workflow:
  name: Karrot Bypass and Login
  description: Complete workflow from bypass setup to successful login
  diagram: |
    START
      ↓
    [Check Device Connection]
      ↓
    [Verify Magisk + Zygisk] ──→ Not installed? → [Call adb-magisk-orchestrator]
      ↓
    [Check PlayIntegrityFork] ──→ Not installed? → [Install PIF Module]
      ↓
    [Launch Karrot App]
      ↓
    [Monitor Logcat for Errors] ──→ Error -18? → [Configure PIF Settings]
      ↓
    [Wait for Login Screen]
      ↓
    [Automate Login Flow] ──→ Failed? → [Screenshot & Report]
      ↓
    [Verify Login Success]
      ↓
    END

decision_tree:
  name: Karrot Automation Decision Flow
  root:
    question: "What is the automation goal?"
    option_bypass_check:
      description: "Check and configure Play Integrity bypass"
      action: "Execute check_detection and bypass_playintegrity"
      requirements: [device_connected, magisk_installed, karrot_installed]
    option_login_test:
      description: "Test login flow with bypass"
      action: "Execute launch_karrot, check_detection, automate_login"
      requirements: [device_connected, bypass_verified, karrot_installed]
    option_full_setup:
      description: "Complete setup from scratch"
      action: "Execute full workflow from Magisk to login"
      requirements: [device_connected, karrot_installed]
    option_monitoring:
      description: "Monitor detection status"
      action: "Execute monitor_logs continuously"
      requirements: [device_connected, karrot_running]

error_handling:
  play_integrity_error_18:
    description: "CLIENT_TRANSIENT_ERROR - emulator detected"
    action: "Verify PlayIntegrityFork module installed and enabled"
    fallback: "Check Zygisk enabled and reboot device"
    recovery: "Configure PIF fingerprint settings for device"

  login_blocked:
    description: "Login blocked due to detection"
    action: "Clear app data and retry with updated bypass"
    fallback: "Check for app updates with stricter detection"
    recovery: "Use alternative device fingerprint"

  app_crash:
    description: "App crashes on launch"
    action: "Check logcat for crash reason"
    fallback: "Reinstall app and retry"
    recovery: "Disable conflicting Magisk modules"

performance_characteristics:
  app_launch_time_seconds: "5-10"
  detection_check_time_seconds: "3-5"
  login_flow_time_seconds: "15-30"
  bypass_verification_time_seconds: "5-10"
  success_rate_with_bypass: "90-95%"
  success_rate_without_bypass: "0-5%"

app_info:
  package_name: "com.towneers.www"
  app_name: "당근마켓 (Karrot)"
  market_url: "https://play.google.com/store/apps/details?id=com.towneers.www"
  detection_type: "Play Integrity API + LIAPP"
  liapp_class: "com.lockincomp.wfcwxdz"
  bypass_difficulty: "Medium-High"
  last_tested: "2025-12-03"

liapp_bypass:
  methodology: "LIAPP security SDK bypass through Zygisk module hooking"
  target_class: "com.lockincomp.wfcwxdz"
  approach:
    - "Hook LIAPP initialization routines"
    - "Spoof integrity check responses"
    - "Hide root/Magisk indicators from LIAPP scans"
    - "Prevent tamper detection callbacks"
  modules_required:
    - name: "PlayIntegrityFork"
      purpose: "Primary integrity bypass"
    - name: "Shamiko"
      purpose: "Root hiding from LIAPP detection"
      required: true
    - name: "HideMyApplist"
      purpose: "Hide Magisk app from detection"
  documentation: ".moai/docs/guides/liapp-bypass/"
```

## Usage Examples

### 1. Check Detection Status
```bash
# Quick detection check
uv run .claude/skills/adb/adb-game-karrot/adb-karrot/scripts/adb-karrot-check-detection.py \
    --device localhost:5555 \
    --check-logcat

# Detailed check with launch
uv run .claude/skills/adb/adb-game-karrot/adb-karrot/scripts/adb-karrot-check-detection.py \
    --device localhost:5555 \
    --launch \
    --detailed
```

### 2. Launch and Monitor
```bash
# Launch Karrot
adb -s localhost:5555 shell am start -n com.towneers.www/.MainActivity

# Monitor logcat for detection
adb -s localhost:5555 logcat | grep -iE "playintegrity|integrity|error.*18|detection"
```

### 3. Complete Bypass Setup
```python
karrot_agent = KarrotAgent(device, magisk_orchestrator, ui_navigator, ocr_finder)

# Step 1: Verify bypass prerequisites
prereq_result = karrot_agent.check_bypass_prerequisites()
if not prereq_result.magisk_ready:
    print("Magisk not ready, running installation...")
    # Delegate to magisk orchestrator

# Step 2: Verify PlayIntegrityFork
pif_result = karrot_agent.verify_playintegrityfork()
if not pif_result.installed:
    print("Installing PlayIntegrityFork module...")
    karrot_agent.install_pif_module()

# Step 3: Launch and check
launch_result = karrot_agent.launch_karrot()
detection_result = karrot_agent.check_detection()

if detection_result.detected:
    print(f"Detection found: {detection_result.detection_type}")
    print(f"Error: {detection_result.error_message}")
else:
    print("Bypass working! App launched successfully.")
```

### 4. Automated Login Flow
```python
# Complete login automation
login_result = karrot_agent.automate_login(
    phone_number="010-1234-5678",
    wait_for_otp=True,
    timeout=60
)

if login_result.success:
    print(f"Login successful: {login_result.user_profile}")
else:
    print(f"Login failed: {login_result.error}")
```

### 5. Continuous Monitoring
```python
# Monitor for detection in real-time
async for event in karrot_agent.monitor_logs():
    if event.is_detection:
        print(f"Detection event: {event.type} at {event.timestamp}")
        # Take action
        await karrot_agent.handle_detection(event)
```

## Integration Points

- **Upstream**: Requires `adb-device-manager` for device connection
- **Upstream**: Requires `adb-magisk-orchestrator` for Magisk/Zygisk setup
- **Upstream**: Requires `adb-bypass` for Play Integrity bypass verification
- **Upstream**: Requires `adb-ui-navigator` for UI automation
- **Upstream**: Requires `adb-ocr-finder` for screen text detection
- **Downstream**: Provides app-specific automation for Karrot marketplace

## Karrot Detection Mechanism

```
Karrot App Detection Stack:
├── Play Integrity API (Primary)
│   ├── deviceIntegrity() check
│   ├── appRecognitionVerdict check
│   └── Error -18: CLIENT_TRANSIENT_ERROR
├── LIAPP Security SDK (Secondary)
│   ├── Class: com.lockincomp.wfcwxdz
│   ├── Tamper detection
│   ├── Root/Magisk detection
│   ├── Integrity verification
│   └── Anti-debugging measures
├── Persona SDK (Wrapper)
│   └── Calls Play Integrity via SDK
├── Build.prop Checks
│   ├── ro.product.model
│   ├── ro.product.manufacturer
│   └── ro.build.fingerprint
└── Emulator Fingerprints
    ├── BlueStacks patterns
    ├── Nox patterns
    └── Generic emulator patterns

Bypass Stack (PlayIntegrityFork + LIAPP):
├── Zygisk Injection
│   ├── Hook Play Services
│   └── Hook LIAPP initialization
├── Device Signature Spoofing
│   └── Replace device fingerprint
├── Integrity Response Spoofing
│   └── Return valid attestation
├── LIAPP Bypass
│   ├── Hook com.lockincomp.wfcwxdz
│   ├── Spoof integrity callbacks
│   └── Hide root indicators
├── Shamiko (Root Hiding)
│   └── Hide Magisk from LIAPP scans
└── Build.prop Override
    └── Spoof device model/manufacturer
```

## LIAPP Bypass Methodology

**LIAPP (Lockin Company)** is a mobile security SDK used by Karrot for additional tamper/root detection.

### Key Detection Points
| Detection Type | LIAPP Method | Bypass Approach |
|---------------|--------------|-----------------|
| Root Detection | Binary scan for su/Magisk | Shamiko hiding |
| Tamper Detection | APK signature verification | Keep original APK |
| Integrity Check | Runtime integrity validation | Hook LIAPP callbacks |
| Debug Detection | Debugger attachment check | Release mode only |

### Monitoring LIAPP Events
```bash
# Monitor LIAPP-related log events
adb logcat | grep -iE "LIAPP|security|tamper|integrity|root|magisk|com.lockincomp"

# Specific LIAPP class monitoring
adb logcat | grep "com.lockincomp.wfcwxdz"
```

### Required Modules for LIAPP Bypass
1. **Shamiko** (Required) - Hides root from LIAPP detection
2. **HideMyApplist** - Hides Magisk Manager from app list queries
3. **PlayIntegrityFork** - Primary integrity bypass

### Documentation Reference
For detailed LIAPP bypass implementation: `.moai/docs/guides/liapp-bypass/`

## Troubleshooting

### Error -18 (CLIENT_TRANSIENT_ERROR)
```bash
# Check PlayIntegrityFork status
adb -s localhost:5555 shell "su -c 'cat /data/adb/modules/playintegrityfix/module.prop'"

# Verify Zygisk enabled
adb -s localhost:5555 shell "su -c 'magisk --sqlite \"SELECT * FROM settings WHERE key=\\\"zygisk\\\"\"'"

# Check logcat for specific errors
adb -s localhost:5555 logcat | grep -i "integrity"
```

### App Crashes on Launch
```bash
# Get crash log
adb -s localhost:5555 logcat -d | grep -E "FATAL|AndroidRuntime|crash"

# Check if Magisk module conflict
adb -s localhost:5555 shell "su -c 'ls /data/adb/modules/'"
```

### Login Blocked
```bash
# Clear app data and retry
adb -s localhost:5555 shell pm clear com.towneers.www

# Verify bypass before retry
uv run .claude/skills/adb/adb-utility/adb-bypass/scripts/preflight-validation.py \
    --device localhost:5555 \
    --detailed
```

## Related Agents

- `adb-device-manager`: Manages device connection and health
- `adb-magisk-orchestrator`: Handles Magisk installation and Zygisk
- `adb-bypass`: Verifies Play Integrity bypass status
- `adb-ui-navigator`: Navigates app UI elements
- `adb-ocr-finder`: Detects text on screen for verification
- `adb-state-verifier`: Verifies app state transitions
