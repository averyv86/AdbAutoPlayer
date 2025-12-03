---
name: adb:bot
description: "Generate and execute game bot"
argument-hint: "[<game-type>|--list|--interactive]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion, Task
model: inherit
---

## Pre-execution Context

!adb devices
!ls -la "$CLAUDE_PROJECT_DIR"/adbautoplayer/src-tauri/src-python/adb_auto_player/games/
!cat "$CLAUDE_PROJECT_DIR"/adbautoplayer/src-tauri/Settings/ADB.toml 2>/dev/null || echo "No ADB config found"

## Essential Files

@.moai/config/config.json
@adbautoplayer/src-tauri/Settings/ADB.toml

---

# ADB Bot Generation and Execution Command

> Purpose: Generate game-specific automation bots from templates, configure parameters, and execute on connected devices with real-time monitoring.
> Tier: Implementation (Bot Development)
> Integration: Combines bot generation, device configuration, and execution orchestration for rapid automation deployment.

## Command Purpose

Generate intelligent game automation bots tailored to specific game types by selecting templates, configuring action sequences, customizing timing parameters, and deploying to connected ADB devices. This command provides an end-to-end workflow from bot scaffolding to execution monitoring, enabling rapid development of Android game automation scripts.

**Core Capabilities:**

- **Bot Generation**: Create game-specific bot skeletons from predefined templates
- **Template Selection**: Choose from arena, farming, quests, events, dailies, and custom patterns
- **Configuration Management**: Customize click sequences, timing delays, and detection thresholds
- **Device Deployment**: Load bot to selected ADB devices with validation
- **Execution Control**: Start, pause, resume, and stop bot operations
- **Performance Monitoring**: Track execution metrics (actions/min, success rate, resource usage)
- **Interactive Workflow**: Guide users through bot creation with step-by-step prompts

---

## Prerequisites

Before running `/adb:bot`, ensure the following requirements are met:

1. **ADB Initialization Complete**: Run `/adb:init` successfully with at least one device configured
2. **Device Connection**: At least one ADB device online and authorized
3. **Game Templates Available**: Template directory exists with game-specific patterns
4. **Configuration Valid**: ADB.toml configuration file present and validated
5. **Python Environment**: Python 3.12+ with adb_auto_player package installed

**Verification Commands:**

```bash
/adb:init --validate    # Verify ADB configuration
adb devices             # Confirm device connectivity
ls adbautoplayer/src-tauri/src-python/adb_auto_player/games/  # Check templates
```

---

## Usage Examples

### Example 1: Interactive Bot Generation (Recommended)

```bash
/adb:bot
```

**Expected Behavior:**
- Presents game type selection menu via AskUserQuestion
- Shows template options (arena, farming, quests, events, dailies)
- Guides through parameter configuration step-by-step
- Generates bot code with customized actions
- Deploys to selected device(s)

### Example 2: Generate Specific Game Type Bot

```bash
/adb:bot arena
```

**Expected Behavior:**
- Uses arena template directly
- Prompts for arena-specific parameters:
  - Battle frequency (battles per hour)
  - Opponent selection strategy (random, weakest, strongest)
  - Formation preset (offensive, defensive, balanced)
  - Reward collection behavior (auto-collect, manual)
- Generates arena bot with configured parameters
- Asks user to confirm before deployment

### Example 3: List Available Templates

```bash
/adb:bot --list
```

**Expected Behavior:**
- Displays all available bot templates in table format
- Shows template details:
  - Template name and description
  - Supported games (AFK Journey, Guitar Girl, etc.)
  - Complexity level (basic, intermediate, advanced)
  - Configuration parameters required
- No bot generation, information only

### Example 4: Custom Bot with Advanced Configuration

```bash
/adb:bot --interactive
```

**Expected Behavior:**
- Activates full interactive mode with detailed configuration
- Presents advanced options:
  - Custom action sequences
  - Dynamic timing adjustments
  - OCR region customization
  - Error handling strategies
  - Retry logic configuration
- Generates highly customized bot
- Validates configuration before deployment

---

## Step-by-Step Workflow

### PHASE 1: Bot Type Selection (5 Steps)

#### Step 1.1: Parse Command Arguments

**Objective:** Determine bot generation mode from command arguments.

**Actions:**
1. Parse `$ARGUMENTS` to extract game type or flags
2. Identify execution mode:
   - **Direct Mode**: Specific game type provided (e.g., `arena`, `farming`)
   - **List Mode**: `--list` flag detected
   - **Interactive Mode**: No arguments or `--interactive` flag
3. Store mode for subsequent steps

**Decision Logic:**
```python
if "--list" in arguments:
    mode = "list"  # Show available templates
elif "--interactive" in arguments or not arguments:
    mode = "interactive"  # Full guided workflow
elif arguments[0] in VALID_GAME_TYPES:
    mode = "direct"  # Generate specific bot type
else:
    mode = "error"  # Invalid argument
```

**Success Criteria:**
- Mode correctly identified
- Invalid arguments detected and reported

**Error Handling:**
- If invalid game type: Suggest using `--list` to see available templates
- If ambiguous arguments: Default to interactive mode with warning

**Output Example:**
```
✓ Command Mode: Interactive
  User will be guided through bot creation workflow
```

---

#### Step 1.2: Verify Prerequisites

**Objective:** Ensure all requirements for bot generation are met.

**Actions:**
1. Check ADB configuration file exists (`ADB.toml`)
2. Verify at least one device configured in device pool
3. Test device connectivity with `adb devices` command
4. Confirm template directory accessible
5. Validate Python environment (adb_auto_player package)

**Success Criteria:**
- ADB.toml found and parseable
- At least one device in "device" state
- Template directory contains valid templates
- Python imports succeed

**Error Handling:**
- If ADB.toml missing: Prompt user to run `/adb:init` first
- If no devices online: Guide user to connect device or start emulator
- If templates missing: Suggest template directory creation
- If imports fail: Check Python dependencies

**Output Example:**
```
✓ Prerequisites Check
  • ADB Config: Found (2 devices configured)
  • Device Connectivity: Online (emulator-5554)
  • Templates: Available (6 templates found)
  • Python Environment: Ready
```

---

#### Step 1.3: List Available Templates (If List Mode)

**Objective:** Display all available bot templates with details.

**Actions:**
1. Scan template directory for bot skeletons
2. Parse template metadata (name, description, complexity)
3. Display templates in rich table format
4. Exit command (no generation)

**Template Discovery:**
```python
template_dir = "adbautoplayer/src-tauri/src-python/adb_auto_player/games/"
templates = [
    {"name": "arena", "game": "AFK Journey", "complexity": "intermediate"},
    {"name": "farming", "game": "AFK Journey", "complexity": "basic"},
    {"name": "quests", "game": "AFK Journey", "complexity": "basic"},
    {"name": "events", "game": "Generic", "complexity": "advanced"},
    {"name": "dailies", "game": "Generic", "complexity": "basic"},
    {"name": "custom", "game": "Any", "complexity": "advanced"}
]
```

**Success Criteria:**
- All templates discovered
- Table displayed with complete information
- Command exits cleanly

**Output Example:**
```
┌─────────────┬─────────────┬────────────┬──────────────────────────┐
│ Template    │ Game        │ Complexity │ Description              │
├─────────────┼─────────────┼────────────┼──────────────────────────┤
│ arena       │ AFK Journey │ Intermediate│ PvP battles, auto-combat│
│ farming     │ AFK Journey │ Basic      │ Resource farming loops   │
│ quests      │ AFK Journey │ Basic      │ Daily quest completion   │
│ events      │ Generic     │ Advanced   │ Event-specific actions   │
│ dailies     │ Generic     │ Basic      │ Daily task automation    │
│ custom      │ Any         │ Advanced   │ Custom action sequences  │
└─────────────┴─────────────┴────────────┴──────────────────────────┘

Use: /adb:bot <template-name> to generate bot
Example: /adb:bot arena
```

---

#### Step 1.4: Select Game Type (Interactive/Direct Mode)

**Objective:** Determine which bot template to use.

**Actions (Interactive Mode):**
1. Use AskUserQuestion tool to present template options
2. Display template descriptions and complexity
3. Allow single selection
4. Store selected template for generation

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Select the game bot type you want to generate:",
        "header": "Bot Template Selection",
        "multiSelect": false,
        "options": [
            {
                "label": "Arena Bot (PvP)",
                "description": "Automated arena battles with opponent selection and formation management"
            },
            {
                "label": "Farming Bot (Resources)",
                "description": "Resource collection loops with stage repeat and loot optimization"
            },
            {
                "label": "Quest Bot (Dailies)",
                "description": "Complete daily quests, claim rewards, and track progress"
            },
            {
                "label": "Event Bot (Limited Time)",
                "description": "Event-specific actions, timing-sensitive tasks"
            },
            {
                "label": "Custom Bot (Advanced)",
                "description": "Create custom action sequence with full control"
            }
        ]
    }]
})
```

**Actions (Direct Mode):**
1. Validate game type against available templates
2. Load template metadata
3. Confirm template selection with user

**Success Criteria:**
- Template selected
- Template exists in template directory
- User confirmed selection (if direct mode)

**Error Handling:**
- If template not found: Show available templates
- If user cancels: Exit gracefully

**Output Example:**
```
✓ Bot Template Selected: Arena Bot (PvP)
  • Game: AFK Journey
  • Complexity: Intermediate
  • Actions: 12 configurable parameters
```

---

#### Step 1.5: Load Template Configuration

**Objective:** Read template file and extract configurable parameters.

**Actions:**
1. Locate template file in games directory
2. Parse template structure (base class, methods, config)
3. Extract configurable parameters:
   - Action sequences (click coordinates, timing)
   - Detection regions (OCR areas, template match)
   - Behavior settings (retry count, timeout)
4. Store default values for user customization

**Template Structure:**
```python
# Example: arena_bot_template.py
class ArenaBot(BaseBot):
    # Configurable parameters
    battles_per_hour = 10  # Default: 10
    opponent_strategy = "random"  # Options: random, weakest, strongest
    formation_preset = "balanced"  # Options: offensive, defensive, balanced
    auto_collect_rewards = True  # Boolean

    def execute_battle_sequence(self):
        # Action sequence with timing
        self.tap(540, 960)  # Battle button
        self.wait(2.0)
        self.tap(100, 100)  # Select opponent
        # ... more actions
```

**Success Criteria:**
- Template loaded successfully
- All configurable parameters identified
- Default values extracted

**Error Handling:**
- If template file missing: Create from base template
- If parsing fails: Use minimal configuration
- If parameters invalid: Apply safe defaults

**Output Example:**
```
✓ Template Configuration Loaded
  • Template File: arena_bot_template.py
  • Configurable Parameters: 12
  • Action Sequences: 5
  • Default Values: Applied
```

---

### PHASE 2: Bot Configuration (4 Steps)

#### Step 2.1: Configure Action Parameters

**Objective:** Customize bot behavior through parameter configuration.

**Actions:**
1. Present configuration interface to user
2. For each configurable parameter:
   - Show parameter name and description
   - Display default value
   - Provide input options (dropdown, slider, text input)
3. Validate user inputs
4. Store custom configuration

**Configuration Categories:**

**Timing Parameters:**
- Action delays (milliseconds between actions)
- Wait timeouts (max wait for screen state)
- Retry intervals (delay between retry attempts)

**Detection Parameters:**
- OCR confidence threshold (0.0-1.0)
- Template match threshold (0.0-1.0)
- Region coordinates (x, y, width, height)

**Behavior Parameters:**
- Max retry attempts (1-10)
- Error recovery strategy (abort, retry, skip)
- Logging level (debug, info, warn, error)

**AskUserQuestion Format (Example - Arena Bot):**

```python
AskUserQuestion({
    "questions": [
        {
            "question": "How many battles per hour should the bot execute?",
            "header": "Battle Frequency",
            "multiSelect": false,
            "options": [
                {"label": "5 battles/hour", "description": "Conservative, low risk of detection"},
                {"label": "10 battles/hour", "description": "Balanced performance (default)"},
                {"label": "15 battles/hour", "description": "Aggressive, high efficiency"}
            ]
        },
        {
            "question": "Select opponent selection strategy:",
            "header": "Opponent Strategy",
            "multiSelect": false,
            "options": [
                {"label": "Random", "description": "Select random opponents"},
                {"label": "Weakest", "description": "Target lowest power opponents"},
                {"label": "Strongest", "description": "Challenge highest power opponents"}
            ]
        }
    ]
})
```

**Success Criteria:**
- All required parameters configured
- Values validated against constraints
- Configuration stored in structured format

**Error Handling:**
- If invalid input: Re-prompt with validation message
- If user skips: Apply default values
- If conflicting parameters: Resolve with safe defaults

**Output Example:**
```
✓ Bot Configuration Complete
  • Battles per hour: 10
  • Opponent strategy: Weakest
  • Formation: Balanced
  • Auto-collect rewards: Yes
  • Action delay: 1500ms
  • Retry attempts: 3
```

---

#### Step 2.2: Configure Detection Regions

**Objective:** Define screen regions for OCR and template matching.

**Actions:**
1. Display device screen resolution
2. Present predefined region templates (based on game)
3. Allow custom region definition (optional)
4. Validate region coordinates (within screen bounds)
5. Store region configuration

**Predefined Regions (AFK Journey Example):**
```python
regions = {
    "battle_button": (450, 1800, 180, 80),  # (x, y, width, height)
    "opponent_list": (50, 400, 980, 1200),
    "rewards_popup": (200, 600, 680, 400),
    "formation_panel": (100, 200, 880, 1600)
}
```

**Custom Region Definition:**
```python
# Interactive mode: Allow user to capture screenshot and mark regions
# Non-interactive: Use predefined regions from template
```

**Success Criteria:**
- All required regions defined
- Coordinates within screen bounds
- No overlapping critical regions

**Error Handling:**
- If invalid coordinates: Clamp to screen bounds
- If region too small: Warn about detection reliability
- If region overlaps: Suggest adjustment

**Output Example:**
```
✓ Detection Regions Configured
  • Battle Button: (450, 1800, 180x80)
  • Opponent List: (50, 400, 980x1200)
  • Rewards Popup: (200, 600, 680x400)
  • Formation Panel: (100, 200, 880x1600)
```

---

#### Step 2.3: Generate Bot Code

**Objective:** Create bot Python file with custom configuration.

**Actions:**
1. Invoke `adb_bot_generator.py` script
2. Pass configuration parameters to generator
3. Generate bot code from template
4. Save to game-specific directory
5. Validate generated code (syntax check)

**Script Invocation:**
```bash
uv run "$CLAUDE_PROJECT_DIR"/.claude/skills/moai-domain-adb/scripts/adb_bot_generator.py \
  --template arena \
  --config bot_config.json \
  --output adbautoplayer/src-tauri/src-python/adb_auto_player/games/afk_journey/custom_routine/arena_bot_generated.py
```

**Generated Bot Structure:**
```python
# Generated by adb_bot_generator.py
# Template: arena
# Generated: 2025-12-01 21:45:00

from adb_auto_player.games.afk_journey.base import AFKJourneyBase

class ArenaBot(AFKJourneyBase):
    """Automated arena bot with custom configuration."""

    def __init__(self, device):
        super().__init__(device)
        # User-configured parameters
        self.battles_per_hour = 10
        self.opponent_strategy = "weakest"
        self.formation_preset = "balanced"
        # ... more parameters

    def execute(self):
        """Main execution loop."""
        self.navigate_to_arena()
        self.select_opponent()
        self.start_battle()
        self.collect_rewards()
```

**Success Criteria:**
- Bot file created successfully
- Valid Python syntax
- All parameters correctly embedded
- File saved to correct directory

**Error Handling:**
- If generator fails: Display detailed error message
- If syntax invalid: Attempt auto-fix or use minimal template
- If write permission denied: Suggest alternate directory

**Output Example:**
```
✓ Bot Code Generated
  • File: arena_bot_generated.py
  • Location: adbautoplayer/src-tauri/src-python/adb_auto_player/games/afk_journey/custom_routine/
  • Lines of Code: 245
  • Syntax: Valid
```

---

#### Step 2.4: Validate Bot Configuration

**Objective:** Ensure generated bot meets quality standards.

**Actions:**
1. Invoke `adb_config_validator.py` script
2. Validate bot configuration:
   - Parameter ranges
   - Region coordinates
   - Device compatibility
3. Run syntax checks
4. Perform dry-run simulation (optional)
5. Report validation results

**Validation Script:**
```bash
uv run "$CLAUDE_PROJECT_DIR"/.claude/skills/moai-domain-adb/scripts/adb_config_validator.py \
  --bot arena_bot_generated.py \
  --device emulator-5554 \
  --dry-run
```

**Validation Checks:**
- Timing parameters within safe ranges (50ms - 10s)
- Detection thresholds valid (0.0 - 1.0)
- Region coordinates within device screen
- Required methods implemented
- No syntax errors

**Success Criteria:**
- All validation checks pass
- Bot ready for deployment
- Warnings addressed or acknowledged

**Error Handling:**
- If critical errors: Block deployment, suggest fixes
- If warnings: Allow deployment with user confirmation
- If dry-run fails: Debug with detailed logs

**Output Example:**
```
✓ Bot Validation Complete
  • Syntax Check: Passed
  • Parameter Validation: Passed
  • Region Check: Passed (4/4 regions valid)
  • Device Compatibility: Compatible with emulator-5554
  • Warnings: 1
    - Action delay <500ms may be detected by anti-bot systems
```

---

### PHASE 3: Device Deployment (3 Steps)

#### Step 3.1: Select Target Device(s)

**Objective:** Choose which device(s) to deploy bot to.

**Actions:**
1. Read device pool from ADB.toml
2. Test device connectivity with `adb devices`
3. Present device selection menu
4. Allow multi-select for batch deployment
5. Store selected device serials

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Select device(s) to deploy bot:",
        "header": "Device Selection",
        "multiSelect": true,
        "options": [
            {
                "label": "emulator-5554 (Emulator, API 34)",
                "description": "Android 14, 1080x2400, 2GB RAM, Online"
            },
            {
                "label": "R58N80ABCDE (Pixel 6, API 33)",
                "description": "Android 13, 1080x2340, 8GB RAM, Online"
            }
        ]
    }]
})
```

**Success Criteria:**
- At least one device selected
- Selected devices online and accessible
- Device serials stored for deployment

**Error Handling:**
- If no device selected: Prompt again
- If device offline: Warn and skip
- If device incompatible: Block deployment

**Output Example:**
```
✓ Target Devices Selected: 1
  • emulator-5554 (Emulator, API 34, Online)
```

---

#### Step 3.2: Deploy Bot to Device(s)

**Objective:** Load bot code and configuration to target devices.

**Actions:**
1. For each selected device:
   - Verify device connection
   - Push bot file to device storage (if needed)
   - Import bot module in Python environment
   - Initialize bot instance with device reference
2. Validate bot loaded successfully
3. Report deployment status

**Deployment Process:**
```python
# Pseudocode for deployment logic
for device_serial in selected_devices:
    device = connect_device(device_serial)
    bot = import_bot("arena_bot_generated.py")
    bot_instance = bot.ArenaBot(device)
    validate_bot_ready(bot_instance)
    log(f"Bot deployed to {device_serial}")
```

**Success Criteria:**
- Bot module imported successfully
- Bot instance initialized with device
- All device connections stable

**Error Handling:**
- If device disconnects during deployment: Retry once, then skip
- If import fails: Check Python path and dependencies
- If initialization fails: Report detailed error

**Output Example:**
```
✓ Bot Deployment Complete
  • Device: emulator-5554
  • Bot: ArenaBot
  • Status: Ready for execution
  • Resources: 45MB memory, 2% CPU
```

---

#### Step 3.3: Pre-Execution Verification

**Objective:** Final checks before bot execution.

**Actions:**
1. Test bot connection to device
2. Verify game is running (optional)
3. Check device state (screen on, unlocked)
4. Run pre-flight test sequence (minimal actions)
5. Display execution readiness status

**Pre-flight Test:**
```python
# Execute minimal test to verify bot functionality
bot.test_tap(540, 960)  # Test tap action
bot.test_screenshot()   # Test screen capture
bot.test_ocr("Test Region")  # Test OCR
```

**Success Criteria:**
- Device responsive to commands
- Screen capture working
- OCR functional
- Bot ready for full execution

**Error Handling:**
- If test fails: Diagnose and report issue
- If game not running: Prompt user to start game
- If device locked: Suggest unlocking device

**Output Example:**
```
✓ Pre-Execution Verification Complete
  • Device Connectivity: Stable
  • Screen Capture: Working (1080x2400)
  • OCR Engine: Ready
  • Game State: Running (AFK Journey detected)
  • Bot Status: Ready to Execute
```

---

### PHASE 4: Bot Execution & Monitoring (5 Steps)

#### Step 4.1: Start Bot Execution

**Objective:** Begin bot automation loop on target device.

**Actions:**
1. Ask user to confirm execution start
2. Display execution parameters summary
3. Start bot main loop
4. Initialize performance tracking
5. Begin real-time monitoring

**Execution Confirmation:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Start bot execution on emulator-5554?",
        "header": "Execution Confirmation",
        "multiSelect": false,
        "options": [
            {
                "label": "Start Bot",
                "description": "Begin automated execution with configured parameters"
            },
            {
                "label": "Review Settings",
                "description": "Return to configuration phase"
            },
            {
                "label": "Cancel",
                "description": "Exit without executing bot"
            }
        ]
    }]
})
```

**Execution Start:**
```python
# Start bot in background process
bot_process = bot.start(async_mode=True)
log(f"Bot started with PID {bot_process.pid}")
```

**Success Criteria:**
- Bot loop started successfully
- Performance tracking initialized
- No immediate errors

**Error Handling:**
- If start fails: Diagnose and report detailed error
- If device disconnects: Attempt reconnection
- If game crashes: Suggest restarting game

**Output Example:**
```
✓ Bot Execution Started
  • Device: emulator-5554
  • Bot: ArenaBot
  • Process ID: 12345
  • Start Time: 2025-12-01 21:50:00
  • Target: 10 battles/hour
```

---

#### Step 4.2: Monitor Execution in Real-Time

**Objective:** Track bot performance and display metrics.

**Actions:**
1. Collect execution metrics:
   - Actions executed (tap count, screenshots taken)
   - Success rate (actions succeeded / total actions)
   - Resource usage (CPU, memory, battery)
   - Errors encountered
2. Display metrics in live table (refresh every 5s)
3. Detect anomalies (high error rate, stuck state)
4. Alert user if intervention needed

**Metrics Display:**
```
═══════════════════════════════════════════════════════════════
                    Bot Execution Monitor
═══════════════════════════════════════════════════════════════
 Device: emulator-5554 | Bot: ArenaBot | Uptime: 00:15:32

 Performance Metrics:
   • Actions Executed: 245 (15.8 actions/min)
   • Battles Completed: 3 of 10
   • Success Rate: 98.4% (241/245 actions succeeded)
   • Average Action Time: 3.8s

 Resource Usage:
   • CPU: 12% | Memory: 58MB | Battery: 85%
   • Network: 2.4 KB/s up, 15.3 KB/s down

 Recent Actions:
   [21:50:15] Navigate to arena
   [21:50:18] Select opponent (Weakest)
   [21:50:22] Start battle
   [21:50:45] Battle complete (Victory)
   [21:50:47] Collect rewards

 Errors: 2
   • [21:50:10] Template match failed (retry successful)
   • [21:50:35] OCR timeout (recovered)

───────────────────────────────────────────────────────────────
 Status: Running | Next Battle: 00:08:30 | Estimated Completion: 22:45:00
═══════════════════════════════════════════════════════════════
```

**Success Criteria:**
- Metrics updating in real-time
- No critical errors
- Bot progressing as expected

**Error Handling:**
- If error rate >10%: Alert user, suggest pause
- If bot stuck: Detect via timeout, offer intervention
- If device disconnects: Pause execution, attempt reconnect

---

#### Step 4.3: Handle Execution Events

**Objective:** Respond to bot events and user input during execution.

**Actions:**
1. Listen for events:
   - Bot errors (OCR failure, template match failure)
   - Device state changes (screen off, app crash)
   - User commands (pause, resume, stop)
2. Process events appropriately
3. Update execution state
4. Log events for analysis

**Event Types:**

**Error Events:**
- OCR timeout → Retry with adjusted parameters
- Template match failure → Fallback to alternate detection
- Device disconnect → Pause and attempt reconnect
- Game crash → Log error, offer restart

**User Commands:**
- Pause → Stop action loop, maintain state
- Resume → Continue from paused state
- Stop → Gracefully terminate execution
- Skip action → Move to next action in sequence

**Success Criteria:**
- Events handled gracefully
- Bot state consistent
- No data loss on interruption

**Error Handling:**
- If unhandled exception: Log stack trace, pause execution
- If critical error: Stop bot, report to user
- If recovery possible: Attempt auto-recovery

**Output Example:**
```
⚠ Event Detected: OCR Timeout
  • Action: Read opponent power level
  • Region: (50, 400, 980x1200)
  • Retry Attempt: 1 of 3
  • Resolution: Increased timeout from 5s to 10s
  • Status: Retry successful
```

---

#### Step 4.4: Generate Performance Report

**Objective:** Compile execution statistics for analysis.

**Actions:**
1. Collect final execution metrics
2. Calculate performance indicators:
   - Total actions executed
   - Success rate percentage
   - Average action time
   - Resource usage statistics
   - Error frequency and types
3. Generate performance report
4. Save report to `.moai/logs/bot-execution-<timestamp>.log`

**Performance Report Format:**
```
═══════════════════════════════════════════════════════════════
                Bot Execution Performance Report
═══════════════════════════════════════════════════════════════

Execution Summary:
  • Bot: ArenaBot
  • Device: emulator-5554 (Emulator, API 34)
  • Start Time: 2025-12-01 21:50:00
  • End Time: 2025-12-01 22:45:32
  • Total Duration: 55m 32s

Performance Metrics:
  • Total Actions: 1,245
  • Successful Actions: 1,223 (98.2%)
  • Failed Actions: 22 (1.8%)
  • Average Action Time: 4.2s
  • Actions per Minute: 22.4

Execution Results:
  • Battles Completed: 10 of 10 (100%)
  • Victories: 9 (90%)
  • Defeats: 1 (10%)
  • Rewards Collected: 10

Resource Usage:
  • Average CPU: 15%
  • Peak Memory: 72MB
  • Battery Consumed: 8%
  • Network Data: 2.4 MB

Error Analysis:
  • Total Errors: 22
  • OCR Timeouts: 12 (recovered: 11)
  • Template Match Failures: 8 (recovered: 7)
  • Device Disconnects: 2 (recovered: 2)
  • Critical Errors: 0

Recommendations:
  ✓ Bot performance excellent (98.2% success rate)
  ⚠ Consider increasing OCR timeout to reduce timeout errors
  ✓ Resource usage within acceptable range

───────────────────────────────────────────────────────────────
Report saved to: .moai/logs/bot-execution-2025-12-01-224532.log
═══════════════════════════════════════════════════════════════
```

**Success Criteria:**
- Report generated successfully
- All metrics captured
- Report saved to logs directory

**Output Example:**
```
✓ Performance Report Generated
  • File: bot-execution-2025-12-01-224532.log
  • Location: .moai/logs/
  • Success Rate: 98.2%
  • Duration: 55m 32s
```

---

#### Step 4.5: Post-Execution Actions

**Objective:** Clean up after bot execution and suggest next steps.

**Actions:**
1. Stop bot process gracefully
2. Release device resources
3. Save execution state (for resume capability)
4. Display completion summary
5. Offer next action options

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Bot execution complete. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Review Performance Report",
                "description": "Analyze execution metrics and recommendations"
            },
            {
                "label": "Run Bot Again",
                "description": "Restart bot with same configuration"
            },
            {
                "label": "Modify Bot Configuration",
                "description": "Adjust parameters and regenerate bot"
            },
            {
                "label": "Generate New Bot",
                "description": "Create different bot type"
            },
            {
                "label": "Exit",
                "description": "Finish bot development session"
            }
        ]
    }]
})
```

**Cleanup Actions:**
```python
bot.stop()
device.release()
save_execution_state("arena_bot_state.json")
log("Bot execution completed")
```

**Success Criteria:**
- Bot stopped cleanly
- Resources released
- State saved (if applicable)
- User presented with next options

**Output Example:**
```
✓ Bot Execution Complete
  • Battles Completed: 10/10
  • Success Rate: 98.2%
  • Duration: 55m 32s
  • Performance Report: .moai/logs/bot-execution-2025-12-01-224532.log

Next steps available via AskUserQuestion menu.
```

---

## Success Criteria

Bot generation and execution is considered successful when ALL of the following conditions are met:

1. **Template Selection**: Valid bot template selected and loaded
2. **Configuration Complete**: All required parameters configured and validated
3. **Code Generation**: Bot Python file generated with valid syntax
4. **Deployment Successful**: Bot loaded to device(s) without errors
5. **Execution Stable**: Bot runs for target duration with acceptable error rate (<5%)
6. **Metrics Captured**: Performance data collected and reported

**Quality Gates:**

- ✓ Bot configuration validated (100% parameter checks pass)
- ✓ Generated code syntax valid (0 syntax errors)
- ✓ Pre-flight tests pass (device communication verified)
- ✓ Execution success rate ≥95%
- ✓ Performance report generated and saved

**Failure Scenarios:**

- ✗ Template not found or invalid
- ✗ Configuration validation fails (critical errors)
- ✗ Device offline or disconnected during deployment
- ✗ Bot execution error rate >10%
- ✗ Critical runtime exception encountered

---

## Metadata

**Tier:** Implementation (Bot Development)

**Required Tools:**
- `adb_bot_generator.py`: Generate bot code from templates
- `adb_config_validator.py`: Validate bot configuration
- `adb_game_tester.py`: Test bot on device (optional)
- `adb_performance_profiler.py`: Profile bot execution (optional)

**Integration Points:**
- Reads: `.moai/config/config.json` (language configuration)
- Reads: `adbautoplayer/src-tauri/Settings/ADB.toml` (device pool)
- Writes: `adbautoplayer/src-tauri/src-python/adb_auto_player/games/<game>/custom_routine/<bot>.py`
- Logs: `.moai/logs/bot-execution-<timestamp>.log`

**Agent Integration:**
- Delegates to: `adb-bot-runner` agent (for execution orchestration)
- Integrates with: moai-domain-adb skill (game-automation, computer-vision modules)

---

## Output Format

### Progress Indicators

Throughout execution, display clear progress indicators:

```
[1/5] Selecting bot template...              ✓ Arena Bot selected
[2/5] Configuring bot parameters...          ✓ 12 parameters configured
[3/5] Generating bot code...                 ✓ arena_bot_generated.py created
[4/5] Deploying to device...                 ✓ Deployed to emulator-5554
[5/5] Starting execution...                  ⏳ Running (3/10 battles complete)
```

### Bot Configuration Summary

Display final configuration before execution:

```yaml
Bot Configuration Summary:
  Template: Arena Bot (PvP)
  Target Device: emulator-5554 (Emulator, API 34)

  Execution Parameters:
    - Battles per hour: 10
    - Opponent strategy: Weakest
    - Formation: Balanced
    - Auto-collect rewards: Yes

  Timing Settings:
    - Action delay: 1500ms
    - Retry attempts: 3
    - Timeout: 30s

  Detection Regions:
    - Battle button: (450, 1800, 180x80)
    - Opponent list: (50, 400, 980x1200)
    - Rewards popup: (200, 600, 680x400)
```

---

## Integration with MoAI Commands

This command fits into the ADB AutoPlayer development workflow:

**Workflow Sequence:**

1. **`/adb:init`** - Initialize ADB project and connect devices
2. **`/adb:bot <game>`** - Generate game-specific bot implementation ← YOU ARE HERE
3. **`/adb:test <bot>`** - Test bot execution and validate behavior
4. **`/adb:deploy <bot>`** - Deploy bot to production environment

**Next Step Recommendations:**

After successful bot generation and initial execution:
- **`/adb:test <bot>`** - Run comprehensive tests on bot
- **Modify bot code** - Edit generated file to customize behavior
- **`/adb:bot`** - Generate another bot for different game type

**Error Recovery:**

If bot generation fails:
- Use `--list` to view available templates
- Check ADB configuration with `/adb:init --validate`
- Review logs in `.moai/logs/` for detailed error messages

---

## Execution Directive

YOU MUST NOW EXECUTE THE COMMAND FOLLOWING THE WORKFLOW DESCRIBED ABOVE.

1. **START PHASE 1**: Parse arguments and verify prerequisites
2. **PROCEED TO PHASE 2**: Configure bot parameters and generate code
3. **PROCEED TO PHASE 3**: Deploy bot to selected device(s)
4. **PROCEED TO PHASE 4**: Execute bot and monitor performance
5. **DO NOT JUST DESCRIBE**: Execute actual tool invocations and script calls

Follow the workflow phases sequentially and report progress to the user.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Architecture:** ADB Domain Command (Implementation Tier)
**Integration:** moai-domain-adb skill, adb_bot_generator script, adb-bot-runner agent
