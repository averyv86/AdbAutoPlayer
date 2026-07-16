# Phase 10 Advanced: Checkpointing, YOLO, & Recording

**Status**: 🟡 In Planning
**Duration Estimate**: 14-18 hours
**Target Completion**: Current session
**Coverage Target**: 85%+ automated tests

---

## Overview

Phase 10 Advanced extends the AdbAutoPlayer with three critical enterprise capabilities:

1. **Checkpointing System** - Save and resume automation from saved states
2. **YOLO Object Detection** - Real-time object detection for game automation
3. **Action Recording** - Record and replay sequences of automation steps

---

## 1️⃣ Checkpointing System

### Purpose
Enable long-running automation to resume from saved states after interruptions, reducing restart time and improving reliability.

### Architecture

```
State Capture → Serialization → Storage → State Restoration → Resume
    ↓              ↓               ↓            ↓             ↓
  FSM State    JSON/Pickle    Disk/DB    Validation      Continue Loop
```

### Core Components

#### CheckpointManager
```python
class CheckpointManager:
    """Manages state checkpointing and recovery"""

    def save_checkpoint(self, state_id: str, state_data: dict, metadata: dict = None) -> str:
        """Save current automation state"""

    def load_checkpoint(self, checkpoint_id: str) -> dict:
        """Load saved checkpoint"""

    def list_checkpoints(self, game: str = None) -> List[Checkpoint]:
        """List available checkpoints"""

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
```

#### StateSerializer
```python
class StateSerializer:
    """Serializes/deserializes automation states"""

    def serialize(self, state: FSMState) -> str:
        """Convert state to JSON/binary"""

    def deserialize(self, data: str) -> FSMState:
        """Restore state from serialized data"""

    def validate(self, state: FSMState) -> ValidationResult:
        """Validate state consistency"""
```

### Checkpoint Format

**JSON Schema**:
```json
{
  "checkpoint_id": "ckpt_afk_20251202_150000_abc123",
  "game": "afk-journey",
  "created_at": "2025-12-02T15:00:00Z",
  "resumed_at": null,
  "duration_seconds": 3600,
  "fsm_state": {
    "current_state": "BATTLING",
    "state_entry_time": "2025-12-02T14:55:30Z",
    "timeout_remaining": 245,
    "iteration": 42,
    "progress": {
      "battles_completed": 15,
      "battles_total": 30,
      "success_rate": 0.93
    }
  },
  "device_state": {
    "serial": "emulator-5554",
    "battery_percent": 85,
    "memory_percent": 62
  },
  "automation_context": {
    "current_target": "battle_button",
    "detection_scale": 1.0,
    "last_action_time": "2025-12-02T14:59:50Z",
    "action_queue": [
      {"action": "tap", "x": 540, "y": 600, "timestamp": "..."}
    ]
  },
  "recovery_state": {
    "failed_attempts": 2,
    "last_error": "template_not_found",
    "recovery_strategy": "scale_fallback"
  },
  "metadata": {
    "hostname": "dev-machine",
    "version": "1.0.0",
    "notes": "Auto-checkpointed at iteration 42"
  }
}
```

### Usage

```bash
# Create checkpoint manually
uv run .claude/skills/moai-domain-adb/scripts/adb_checkpoint_manager.py \
  --game afk-journey \
  --device emulator-5554 \
  --save-checkpoint

# List available checkpoints
uv run .claude/skills/moai-domain-adb/scripts/adb_checkpoint_manager.py \
  --list-checkpoints \
  --game afk-journey

# Resume from checkpoint
uv run .claude/skills/moai-domain-adb/scripts/adb_checkpoint_manager.py \
  --game afk-journey \
  --load-checkpoint ckpt_afk_20251202_150000_abc123
```

---

## 2️⃣ YOLO Object Detection

### Purpose
Real-time object detection for dynamic game automation, enabling detection of game elements without pre-captured templates.

### Architecture

```
Screen Capture → YOLO Inference → Bounding Boxes → Action Execution
     ↓              ↓                    ↓              ↓
  Screenshot   YOLOv8 Model    Element Locations   Tap/Swipe
```

### Core Components

#### YOLODetector
```python
class YOLODetector:
    """YOLO-based object detection"""

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects in frame"""

    def detect_classes(self, frame: np.ndarray, classes: List[str]) -> List[Detection]:
        """Detect specific object classes"""

    def track(self, frames: List[np.ndarray]) -> List[Track]:
        """Track objects across frames"""
```

#### Detection Data Structure
```python
@dataclass
class Detection:
    """YOLO detection result"""
    class_id: int
    class_name: str
    confidence: float  # 0.0-1.0
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    mask: Optional[np.ndarray] = None  # Segmentation mask
    track_id: Optional[int] = None  # For tracking across frames
```

### Supported Models

| Model | Size | Speed | Accuracy | Memory |
|-------|------|-------|----------|--------|
| YOLOv8n | Nano | ⚡⚡⚡ | Good | <50MB |
| YOLOv8s | Small | ⚡⚡ | Very Good | ~100MB |
| YOLOv8m | Medium | ⚡ | Excellent | ~200MB |
| YOLOv8l | Large | Slow | Outstanding | ~500MB |

### Training Custom Models

**Supported Game Classes**:
- AFK Journey: hero, enemy, battle_button, item, altar
- Guitar Girl: note, combo_counter, timing_indicator
- Karrot: profile_button, listing, chat_icon

### Usage

```bash
# Run YOLO detection
uv run .claude/skills/moai-domain-adb/scripts/adb_yolo_detector.py \
  --device emulator-5554 \
  --model yolov8m \
  --confidence-threshold 0.5 \
  --output toon

# Detect specific classes
uv run .claude/skills/moai-domain-adb/scripts/adb_yolo_detector.py \
  --device emulator-5554 \
  --classes hero,enemy,battle_button \
  --output json

# Track objects across frames
uv run .claude/skills/moai-domain-adb/scripts/adb_yolo_detector.py \
  --device emulator-5554 \
  --enable-tracking \
  --track-frames 30
```

---

## 3️⃣ Action Recording & Playback

### Purpose
Record sequences of automation steps for analysis, debugging, and playback on different devices.

### Architecture

```
User Actions → Recording Engine → Action Sequence Storage → Playback Executor
     ↓               ↓                     ↓                      ↓
  FSM Events    Action Logger        JSON/YAML            Execute Recorded Actions
```

### Action Recording Format

```yaml
# recording-afk-journey-quest-001.yaml
---
metadata:
  game: afk-journey
  device: emulator-5554
  created_at: 2025-12-02T15:00:00Z
  duration: 180.5
  source: "auto-recording"
  environment:
    resolution: "1280x720"
    api_level: 33
    device_model: "Android Emulator"

actions:
  - timestamp: 0.0
    type: screen_capture
    params:
      output_path: "/tmp/frame_000.png"

  - timestamp: 0.5
    type: template_detect
    params:
      template: "quest_start_button.png"
      confidence: 0.95
      location: [540, 600]

  - timestamp: 1.0
    type: tap
    params:
      x: 540
      y: 600
      duration: 0.1

  - timestamp: 2.0
    type: wait
    params:
      duration: 1.5
      condition: "quest_battle_screen_visible"

  - timestamp: 3.5
    type: ocr
    params:
      region: [100, 50, 700, 150]
      expected_text: "Quest Progress"
      confidence: 0.8

  - timestamp: 4.0
    type: checkpoint
    params:
      checkpoint_id: "ckpt_quest_midpoint"
      description: "Quest started successfully"

replay_strategy:
  device_resolution_fallback: true
  template_scale_matching: true
  adaptive_timing: true
  error_recovery: true
```

### Core Components

#### ActionRecorder
```python
class ActionRecorder:
    """Records automation actions"""

    def start_recording(self) -> str:
        """Start recording session"""

    def record_action(self, action: AutomationAction):
        """Record single action"""

    def stop_recording(self, output_path: str) -> str:
        """Stop recording and save"""

    def pause_recording(self):
        """Pause recording temporarily"""
```

#### ActionPlayer
```python
class ActionPlayer:
    """Plays back recorded actions"""

    def load_recording(self, recording_path: str) -> List[AutomationAction]:
        """Load recorded actions"""

    def play(self, device: str) -> PlaybackResult:
        """Execute recorded actions"""

    def play_step_by_step(self, device: str) -> Iterator[PlaybackStep]:
        """Play with step-by-step control"""
```

### Usage

```bash
# Record actions
uv run .claude/skills/moai-domain-adb/scripts/adb_action_recorder.py \
  --device emulator-5554 \
  --game afk-journey \
  --record \
  --output-file recording.yaml

# Play back recording
uv run .claude/skills/moai-domain-adb/scripts/adb_action_player.py \
  --device emulator-5554 \
  --replay recording.yaml \
  --adaptive-timing \
  --resolution-fallback

# Analyze recording
uv run .claude/skills/moai-domain-adb/scripts/adb_action_analyzer.py \
  --input recording.yaml \
  --output report.json
```

---

## Implementation Plan

### Phase 10a: Checkpointing (4-5 hours)
1. Implement CheckpointManager class
2. Implement StateSerializer (JSON format)
3. Create checkpoint storage (filesystem-based)
4. Implement checkpoint validation
5. Add checkpoint CLI script (adb_checkpoint_manager.py)
6. Create 20+ tests

### Phase 10b: YOLO Detection (5-6 hours)
1. Setup YOLOv8 integration
2. Implement YOLODetector class
3. Add inference pipeline with caching
4. Implement class detection and filtering
5. Create YOLO CLI script (adb_yolo_detector.py)
6. Add performance optimizations
7. Create 25+ tests

### Phase 10c: Action Recording (5-7 hours)
1. Implement ActionRecorder class
2. Implement ActionPlayer class
3. Create recording format serialization
4. Add playback strategy (adaptive timing)
5. Implement action analyzer
6. Create recording CLI script (adb_action_recorder.py)
7. Create 30+ tests

---

## Configuration (Phase 10)

### checkpoint-config.toml
```toml
[storage]
enabled = true
location = ".moai/checkpoints"
auto_checkpoint_interval = 300  # seconds
max_checkpoints_per_game = 5

[validation]
validate_on_load = true
validate_device_compatibility = true

[cleanup]
auto_cleanup = true
retention_days = 7
```

### yolo-config.toml
```toml
[model]
version = "yolov8m"
confidence_threshold = 0.5
iou_threshold = 0.45
max_detections = 100

[classes]
afk_journey = ["hero", "enemy", "battle_button", "item"]
guitar_girl = ["note", "combo_counter", "timing"]
karrot = ["profile_button", "listing", "chat"]

[performance]
use_gpu = true
batch_size = 1
num_workers = 0
```

### recording-config.toml
```toml
[recording]
auto_save = true
save_interval = 60  # seconds
max_recording_duration = 3600

[playback]
adaptive_timing = true
error_recovery = true
resolution_fallback = true
template_scale_matching = true
```

---

## Test Coverage Target

| Component | Tests | Coverage |
|-----------|-------|----------|
| CheckpointManager | 25+ | 88% |
| YOLODetector | 30+ | 85% |
| ActionRecorder | 20+ | 87% |
| ActionPlayer | 20+ | 86% |
| StateSerializer | 15+ | 90% |
| **TOTAL** | **110+** | **87%** |

---

## Success Metrics

✅ **Functionality**
- Checkpointing: Save/load/list/delete working
- YOLO: Detect/track/classify working
- Recording: Record/play/analyze working

✅ **Performance**
- Checkpoint save: <100ms
- Checkpoint load: <200ms
- YOLO inference: <50ms (YOLOv8n)
- Recording playback: Real-time capable

✅ **Reliability**
- All 110+ tests passing
- Cross-device compatibility
- Error recovery >95% success rate

---

## Next Steps After Phase 10

**Future Enhancements**:
- Multi-device synchronized automation
- Cloud-based checkpoint storage
- YOLO model training pipeline
- Web UI for recording playback
- Distributed execution framework

---

*Phase 10 Advanced Specification | Created: 2025-12-02*
