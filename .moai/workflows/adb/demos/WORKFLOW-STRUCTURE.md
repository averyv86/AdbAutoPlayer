# Bluestacks Demo Workflow - Visual Structure

**File**: bluestacks-demo.toon
**Version**: 1.0.0
**Last Updated**: 2025-12-02

---

## Workflow Execution Flow

```
START
  │
  └─→ PHASE 1: Connection and Device Information
      │
      ├─→ Step 1.1: Connect to Device
      │   └─ Action: execute connect.yaml
      │   └─ Params: device, timeout=10
      │   └─ Retry: 3 attempts (2s delay)
      │
      ├─→ Step 1.2: Verify Connection
      │   └─ Action: run verify-connection.py
      │   └─ Validation: connection_status output
      │
      ├─→ Step 1.3: Get Device Info
      │   └─ Action: run get-device-info.py
      │   └─ Output: device_model, android_version, resolution, manufacturer
      │
      ├─→ Step 1.4: Display Device Table
      │   └─ Format: Human-readable table
      │   └─ Columns: Model, Android Version, Resolution, Manufacturer
      │
      └─→ CHECKPOINT 1 [Resumable from here]

         │
         └─→ PHASE 2: Display Specifications
             │
             ├─→ Step 2.1: Get Display Info
             │   └─ Action: run get-display-info.py
             │   └─ Output: display_width, display_height, display_density, display_orientation
             │
             ├─→ Step 2.2: Display Specs Table
             │   └─ Format: Human-readable table
             │   └─ Columns: Width, Height, Density, Orientation
             │
             └─→ CHECKPOINT 2 [Resumable from here]

                │
                └─→ PHASE 3: Interactive Control Demo (LOOP-BASED)
                    │
                    LOOP DEFINITION:
                    ├─ Type: items
                    ├─ Count: 3 (tap_1, tap_2, tap_3)
                    └─ Items:
                       ├─ tap_1: (x=540, y=960) - Center Screen Tap
                       ├─ tap_2: (x=200, y=400) - Top-Left Corner Tap
                       └─ tap_3: (x=880, y=1520) - Bottom-Right Corner Tap
                    │
                    ├─→ ITERATION 1: tap_1
                    │   ├─→ Step 3.1: Execute Tap at (540, 960)
                    │   │   └─ Action: tap.py --x 540 --y 960
                    │   │   └─ Log: Tap 1/3 - Center Screen Tap successful
                    │   │
                    │   └─→ Step 3.2: Wait Between Taps [condition: 1 < 3]
                    │       └─ Duration: 1 second (configurable)
                    │
                    ├─→ ITERATION 2: tap_2
                    │   ├─→ Step 3.1: Execute Tap at (200, 400)
                    │   │   └─ Action: tap.py --x 200 --y 400
                    │   │   └─ Log: Tap 2/3 - Top-Left Corner Tap successful
                    │   │
                    │   └─→ Step 3.2: Wait Between Taps [condition: 2 < 3]
                    │       └─ Duration: 1 second
                    │
                    ├─→ ITERATION 3: tap_3
                    │   ├─→ Step 3.1: Execute Tap at (880, 1520)
                    │   │   └─ Action: tap.py --x 880 --y 1520
                    │   │   └─ Log: Tap 3/3 - Bottom-Right Corner Tap successful
                    │   │
                    │   └─→ Step 3.2: Wait Between Taps [condition: 3 < 3 = FALSE]
                    │       └─ SKIPPED (no wait after last iteration)
                    │
                    METRICS:
                    ├─ total_taps: 3
                    ├─ successful_taps: 3
                    ├─ failed_taps: 0
                    └─ success_rate: 100%
                    │
                    └─→ CHECKPOINT 3 [Resumable from here]

                       │
                       └─→ PHASE 4: Screenshot Capture
                           │
                           ├─→ Step 4.1: Take Screenshot
                           │   └─ Action: screenshot.py
                           │   └─ Output: /tmp/bluestacks-demo-{{ timestamp }}.png
                           │   └─ Format: PNG
                           │
                           ├─→ Step 4.2: Verify Screenshot File
                           │   └─ Check: exists, readable, min_size >= 1000 bytes
                           │
                           ├─→ Step 4.3: Display Screenshot
                           │   └─ Format: Image display (50% width)
                           │
                           └─→ CHECKPOINT 4 [Resumable from here]

                              │
                              └─→ PHASE 5: Swipe Gesture Demo (LOOP-BASED)
                                  │
                                  LOOP DEFINITION:
                                  ├─ Type: items
                                  ├─ Count: 2 (swipe_1, swipe_2)
                                  └─ Items:
                                     ├─ swipe_1: direction=up, start_y=1400, end_y=600
                                     └─ swipe_2: direction=down, start_y=600, end_y=1400
                                  │
                                  ├─→ ITERATION 1: swipe_1 (UP)
                                  │   ├─→ Step 5.1: Execute UP Swipe
                                  │   │   └─ Action: swipe.py --direction up
                                  │   │   └─ Duration: 500ms
                                  │   │   └─ Log: Swipe 1/2 - UP successful
                                  │   │
                                  │   └─→ Step 5.2: Wait Between Swipes [condition: 1 < 2]
                                  │       └─ Duration: 1.5 seconds (configurable)
                                  │
                                  ├─→ ITERATION 2: swipe_2 (DOWN)
                                  │   ├─→ Step 5.1: Execute DOWN Swipe
                                  │   │   └─ Action: swipe.py --direction down
                                  │   │   └─ Duration: 500ms
                                  │   │   └─ Log: Swipe 2/2 - DOWN successful
                                  │   │
                                  │   └─→ Step 5.2: Wait Between Swipes [condition: 2 < 2 = FALSE]
                                  │       └─ SKIPPED (no wait after last iteration)
                                  │
                                  METRICS:
                                  ├─ total_swipes: 2
                                  ├─ successful_swipes: 2
                                  ├─ failed_swipes: 0
                                  └─ success_rate: 100%
                                  │
                                  └─→ CHECKPOINT 5 [Resumable from here]

                                     │
                                     └─→ VALIDATION
                                         ├─ Check: device_parameter_valid (IP:port format)
                                         ├─ Check: output_folder_exists (writable)
                                         ├─ Check: all_phases_completed (all succeeded)
                                         └─ Check: minimum_phase_success_rate (≥80%)

                                        │
                                        └─→ RECOVERY & CLEANUP
                                            ├─ close_connection (gracefully)
                                            └─ cleanup_temp_files (if needed)

                                           │
                                           └─→ OUTPUT AGGREGATION
                                               ├─ demo_summary (JSON)
                                               ├─ phase_results (all phases)
                                               └─ metrics (success rates)

                                              │
                                              └─→ END
                                                  ├─ Status: SUCCESS or PARTIAL SUCCESS
                                                  ├─ Duration: Total execution time
                                                  └─ Report: Generated JSON summary
```

---

## Parameter Flow

```
PARAMETERS (Input)
├─ device: "127.0.0.1:5555"
├─ screenshot_dir: "/tmp"
├─ tap_wait_duration: 1 (seconds)
└─ swipe_wait_duration: 1.5 (seconds)

    │
    └─→ VARIABLE SUBSTITUTION
        ├─ Phase 1: {{ parameters.device }}
        ├─ Phase 3 Loop: {{ parameters.tap_wait_duration }}
        ├─ Phase 4: {{ parameters.screenshot_dir }}
        └─ Phase 5 Loop: {{ parameters.swipe_wait_duration }}
```

---

## Loop Variable Substitution

### Phase 3: Tap Loop

```
PHASE 3 LOOP ITEMS:
├─ tap_1: { x: 540, y: 960 }
├─ tap_2: { x: 200, y: 400 }
└─ tap_3: { x: 880, y: 1520 }

SUBSTITUTION IN LOOP STEPS:
├─ {{ item.x }}           → 540, 200, 880 (per iteration)
├─ {{ item.y }}           → 960, 400, 1520 (per iteration)
├─ {{ item.description }} → "Center...", "Top-Left...", "Bottom-Right..."
├─ {{ loop.index }}       → 1, 2, 3
└─ {{ loop.total }}       → 3, 3, 3

EXECUTION:
Iteration 1: tap 540,960 wait 1s
Iteration 2: tap 200,400 wait 1s
Iteration 3: tap 880,1520 [no wait]
```

### Phase 5: Swipe Loop

```
PHASE 5 LOOP ITEMS:
├─ swipe_1: { direction: "up", start_y: 1400, end_y: 600 }
└─ swipe_2: { direction: "down", start_y: 600, end_y: 1400 }

SUBSTITUTION IN LOOP STEPS:
├─ {{ item.direction }}    → "up", "down"
├─ {{ item.start_y }}      → 1400, 600
├─ {{ item.end_y }}        → 600, 1400
├─ {{ loop.index }}        → 1, 2
└─ {{ loop.total }}        → 2, 2

EXECUTION:
Iteration 1: swipe up (1400→600) wait 1.5s
Iteration 2: swipe down (600→1400) [no wait]
```

---

## Output Variable Flow

```
PHASE OUTPUTS:
├─ Phase 1 outputs:
│  ├─ device_model
│  ├─ android_version
│  ├─ resolution
│  └─ manufacturer
│
├─ Phase 2 outputs:
│  ├─ display_width
│  ├─ display_height
│  ├─ display_density
│  └─ display_orientation
│
├─ Phase 3 metrics:
│  ├─ total_taps
│  ├─ successful_taps
│  ├─ failed_taps
│  └─ success_rate
│
├─ Phase 4 outputs:
│  ├─ screenshot_path
│  └─ screenshot_size
│
└─ Phase 5 metrics:
   ├─ total_swipes
   ├─ successful_swipes
   ├─ failed_swipes
   └─ success_rate

    │
    └─→ FINAL OUTPUT AGGREGATION
        └─ demo_summary (JSON)
           ├─ workflow_name
           ├─ workflow_version
           ├─ execution_date
           ├─ target_device
           ├─ total_execution_time_seconds
           ├─ phases_executed (all 5 with results)
           ├─ overall_success
           └─ notes
```

---

## Conditional Execution Flow

### Wait Steps (Conditional)

```
PHASE 3 LOOP - WAIT CONDITION:
condition: {{ loop.index < loop.total }}

Iteration 1: {{ 1 < 3 }} = TRUE  → EXECUTE wait 1s
Iteration 2: {{ 2 < 3 }} = TRUE  → EXECUTE wait 1s
Iteration 3: {{ 3 < 3 }} = FALSE → SKIP wait

BENEFIT: No unnecessary wait after last iteration
```

---

## Phase Dependencies

```
Phase 1 ✓ (Connection)
    │
    └─→ Phase 2 depends on Phase 1
        ├─ Cannot start if Phase 1 fails
        └─ Can only proceed after Phase 1 succeeds

        │
        └─→ Phase 3 depends on Phase 2
            ├─ Cannot start if Phase 2 fails
            └─ Can only proceed after Phase 2 succeeds

            │
            └─→ Phase 4 depends on Phase 3
                ├─ Cannot start if Phase 3 fails
                └─ Can only proceed after Phase 3 succeeds

                │
                └─→ Phase 5 depends on Phase 4
                    ├─ Cannot start if Phase 4 fails
                    └─ Can only proceed after Phase 4 succeeds
```

---

## Error Recovery Flow

```
PHASE FAILURE
    │
    ├─→ Phase 1-2: RETRY
    │   ├─ Max Attempts: 3
    │   ├─ Backoff: 1.5x multiplier
    │   └─ Delays: 2s, 3s, 4.5s
    │
    ├─→ Phase 3-5 Loop Failures: CONTINUE
    │   ├─ Continue to next iteration
    │   ├─ Log failure
    │   └─ Update metrics
    │
    └─→ Critical Failures: CLEANUP
        ├─ Close connection
        ├─ Clean temp files
        └─ Generate error report
```

---

## Success Rate Validation

```
VALIDATION RULE:
minimum_phase_success_rate >= 0.8 (80%)

Phase 3 Calculation:
├─ If 3/3 taps succeed: 100% ✓ PASS
├─ If 2/3 taps succeed: 67% ✗ FAIL
└─ If 3/3 taps succeed: 100% ✓ PASS

Result: Phase succeeds if ≥ 80% of iterations succeed
```

---

## Metric Collection Flow

### Phase 3 (Taps)

```
LOOP METRICS TRACKING:
├─ Iteration 1: Tap ✓ → successful_taps = 1
├─ Iteration 2: Tap ✓ → successful_taps = 2
└─ Iteration 3: Tap ✓ → successful_taps = 3

FINAL METRICS:
├─ total_taps: 3
├─ successful_taps: 3
├─ failed_taps: 0
└─ success_rate: 3/3 * 100 = 100%

VALIDATION:
├─ success_rate (100%) >= required (80%) ✓ PASS
└─ Phase 3: SUCCESS
```

### Phase 5 (Swipes)

```
LOOP METRICS TRACKING:
├─ Iteration 1: Swipe ✓ → successful_swipes = 1
└─ Iteration 2: Swipe ✓ → successful_swipes = 2

FINAL METRICS:
├─ total_swipes: 2
├─ successful_swipes: 2
├─ failed_swipes: 0
└─ success_rate: 2/2 * 100 = 100%

VALIDATION:
├─ success_rate (100%) >= required (80%) ✓ PASS
└─ Phase 5: SUCCESS
```

---

## File Reference Flow

```
bluestacks-demo.toon
├─→ !include ../steps/connection/connect.yaml
│   └─ References: .moai/workflows/adb/steps/connection/connect.yaml
│
├─→ Script: get-device-info.py
│   └─ References: .claude/skills/moai-domain-adb/scripts/capture/get-device-info.py
│
├─→ Script: get-display-info.py
│   └─ References: .claude/skills/moai-domain-adb/scripts/capture/get-display-info.py
│
├─→ Script: tap.py
│   └─ References: .claude/skills/moai-domain-adb/scripts/control/tap.py
│
├─→ Script: screenshot.py
│   └─ References: .claude/skills/moai-domain-adb/scripts/capture/screenshot.py
│
├─→ Script: swipe.py
│   └─ References: .claude/skills/moai-domain-adb/scripts/control/swipe.py
│
└─→ Output: bluestacks-demo-report-{{ timestamp }}.md
    └─ Location: .moai/workflows/adb/demos/outputs/
```

---

## Checkpoint Resume Points

```
WORKFLOW WITH 5 CHECKPOINTS:

Execution 1:
├─→ Phase 1 [Checkpoint 1] ✓
├─→ Phase 2 [Checkpoint 2] ✓
├─→ Phase 3 [Checkpoint 3] ✗ FAILED

Later Resume:
├─→ Phase 3 [Checkpoint 3] ← RESUME HERE
├─→ Phase 4 [Checkpoint 4] ✓
├─→ Phase 5 [Checkpoint 5] ✓
└─→ SUCCESS

BENEFIT: No need to re-run successful phases
```

---

## Execution Timeline Example

```
TIME    PHASE   EVENT                                    DURATION
00:00   Start   Initialize workflow                      -
00:05   P1      Connect to device                        5s
00:10   P1      Verify connection                        5s
00:15   P1      Get device info                          5s
00:20   P1      Display table                            3s
        [Checkpoint 1]
00:25   P2      Get display info                         5s
00:30   P2      Display specs table                      3s
        [Checkpoint 2]
00:35   P3-L1   Tap at 540,960                          2s
00:37   P3      Wait between taps                        1s
00:38   P3-L2   Tap at 200,400                          2s
00:40   P3      Wait between taps                        1s
00:41   P3-L3   Tap at 880,1520                         2s
        [Checkpoint 3]
00:45   P4      Take screenshot                         10s
00:50   P4      Verify screenshot                       3s
00:55   P4      Display screenshot                      2s
        [Checkpoint 4]
01:00   P5-L1   Swipe UP                               2s
01:02   P5      Wait between swipes                     1.5s
01:03.5 P5-L2   Swipe DOWN                             2s
        [Checkpoint 5]
01:06   End     Generate summary report                1s

TOTAL EXECUTION TIME: ~106 seconds (1m 46s)
```

---

## Token Efficiency

```
bluestacks-demo.toon:
├─ File size: ~17 KB
├─ Lines: ~550
├─ YAML format: TOON v4.0
└─ Estimated tokens: ~3,500

Equivalent JSON would be:
├─ File size: ~22 KB
├─ Lines: ~900
└─ Estimated tokens: ~5,500

SAVINGS: 36% reduction (2,000 tokens saved)
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete Visual Reference
