# ADB Game Bot Scaffolding Framework

**Version**: 1.0.0
**Status**: ✅ Production Ready
**Focus**: Game automation bot patterns and templates

---

## Overview

Game bot scaffolding provides specialized templates and patterns for creating automated game bots with state management, vision-based element detection, recovery strategies, and performance optimization.

### Key Components

1. **State Management**: FSM-based bot state tracking
2. **Vision Automation**: Template matching + OCR detection
3. **Recovery Patterns**: Error recovery and fallback strategies
4. **Performance Optimization**: Speed and efficiency improvements

---

## 1. Game State Manager Pattern

### State Machine Definition

```python
from enum import Enum

class BotState(Enum):
    IDLE = "idle"
    CHECKING = "checking"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ERROR = "error"
    RECOVERY = "recovery"
```

### Implementation Template

```python
class StateManager:
    def __init__(self):
        self.current_state = BotState.IDLE
        self.state_entry_time = time.time()
        self.state_timeout = 30  # seconds
        self.history = []

    def transition(self, new_state: BotState):
        """Transition to new state with logging"""
        self.history.append({
            'from': self.current_state.value,
            'to': new_state.value,
            'time': time.time()
        })
        self.current_state = new_state
        self.state_entry_time = time.time()

    def is_timeout(self) -> bool:
        """Check state timeout"""
        elapsed = time.time() - self.state_entry_time
        return elapsed > self.state_timeout
```

### State Transitions

```
IDLE → CHECKING → EXECUTING → VALIDATING → COMPLETED
                      ↓
                    ERROR → RECOVERY → CHECKING (retry)
```

---

## 2. Vision-Based Element Detection

### Template Matching

```python
import cv2

class TemplateDetector:
    def __init__(self, template_path: str):
        self.template = cv2.imread(template_path)

    def detect(self, frame, threshold=0.8) -> Optional[Tuple[int, int]]:
        """Detect template in frame"""
        result = cv2.matchTemplate(
            frame, self.template,
            cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            return max_loc
        return None
```

### OCR-Based Detection

```python
import pytesseract
from PIL import Image

class OCRDetector:
    def detect_text(self, region) -> str:
        """Extract text via OCR"""
        return pytesseract.image_to_string(Image.fromarray(region))

    def find_text(self, frame, target_text: str) -> bool:
        """Check if text exists in frame"""
        text = self.detect_text(frame)
        return target_text.lower() in text.lower()
```

### Multi-Method Fallback

```python
class VisionOrchestrator:
    def __init__(self, device):
        self.template_detector = TemplateDetector(...)
        self.ocr_detector = OCRDetector()
        self.device = device

    def find_element(self, frame, element_id: str):
        """Try multiple detection methods"""
        # Try template matching first (fast)
        if location := self.template_detector.detect(frame):
            return location

        # Fall back to OCR (slower but more flexible)
        if self.ocr_detector.find_text(frame, element_id):
            return self._estimate_location(frame, element_id)

        return None
```

---

## 3. Recovery Patterns

### Exponential Backoff Retry

```python
import time

class RetryStrategy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args, **kwargs):
        """Execute with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
```

### Fallback Chain Strategy

```python
class FallbackChain:
    def __init__(self, strategies: List[Callable]):
        self.strategies = strategies

    def execute(self, *args, **kwargs):
        """Try strategies in order"""
        errors = []
        for strategy in self.strategies:
            try:
                return strategy(*args, **kwargs)
            except Exception as e:
                errors.append(str(e))
                continue

        raise Exception(f"All strategies failed: {errors}")
```

### State Reset Recovery

```python
class RecoveryExecutor:
    def __init__(self, device):
        self.device = device

    def reset_to_home(self):
        """Return to home screen"""
        self.device.press_home()
        time.sleep(2)

    def force_close_app(self, package_name: str):
        """Force close and restart"""
        self.device.close_app(package_name)
        time.sleep(3)
        self.device.open_app(package_name)

    def full_reset(self, package_name: str):
        """Complete reset procedure"""
        self.force_close_app(package_name)
        self.reset_to_home()
```

---

## 4. Performance Optimization

### Caching Strategies

```python
from functools import lru_cache

class CachedDetector:
    @lru_cache(maxsize=128)
    def load_template(self, template_path: str):
        """Cache loaded templates"""
        return cv2.imread(template_path)

    def detect_cached(self, frame, template_path: str):
        """Use cached template"""
        template = self.load_template(template_path)
        return cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

class ParallelDetector:
    def detect_multiple(self, frame, templates: List[str]):
        """Detect multiple templates in parallel"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self._detect, frame, t)
                for t in templates
            ]
            return [f.result() for f in futures]
```

### Lazy Initialization

```python
class LazyInitializer:
    def __init__(self):
        self._resource = None

    @property
    def resource(self):
        if self._resource is None:
            self._resource = self._initialize()
        return self._resource

    def _initialize(self):
        # Expensive initialization
        pass
```

---

## 5. Complete Bot Example

```python
class GameBot:
    def __init__(self, device, game_name: str):
        self.device = device
        self.state_manager = StateManager()
        self.detector = VisionOrchestrator(device)
        self.recovery = RecoveryExecutor(device)
        self.retry = RetryStrategy(max_retries=3)
        self.game = game_name

    def execute(self, max_iterations=None):
        """Main bot execution loop"""
        iteration = 0

        while True:
            # Phase 1: Check status
            self.state_manager.transition(BotState.CHECKING)
            frame = self.device.capture()

            if not self._verify_game_active(frame):
                break

            # Phase 2: Execute action
            self.state_manager.transition(BotState.EXECUTING)
            try:
                self.retry.execute_with_retry(self._execute_action, frame)
            except Exception as e:
                self.state_manager.transition(BotState.ERROR)
                self.recovery.reset_to_home()
                self.state_manager.transition(BotState.RECOVERY)
                continue

            # Phase 3: Validate result
            self.state_manager.transition(BotState.VALIDATING)
            if self._validate_action():
                self.state_manager.transition(BotState.COMPLETED)
            else:
                self.state_manager.transition(BotState.ERROR)
                continue

            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break

            time.sleep(0.1)

    def _execute_action(self, frame):
        """Execute single action"""
        location = self.detector.find_element(frame, "action_button")
        if location:
            self.device.tap(location[0], location[1])

    def _validate_action(self) -> bool:
        """Validate action result"""
        frame = self.device.capture()
        return self.detector.find_element(frame, "success_indicator") is not None
```

---

## 6. Configuration YAML

```yaml
game_bot:
  state_timeouts:
    checking: 10
    executing: 60
    validating: 15
    recovery: 30

  retry:
    max_retries: 3
    base_delay: 1.0
    max_backoff: 30

  vision:
    template_threshold: 0.85
    ocr_fallback: true
    cache_enabled: true

  recovery:
    auto_recovery: true
    reset_on_error: true
    max_recovery_attempts: 3
```

---

## Best Practices

✅ **DO**:
- Use state machines for clear flow control
- Implement multi-method detection (template + OCR)
- Add timeouts to prevent infinite loops
- Create recovery procedures for all error states
- Cache expensive computations

❌ **DON'T**:
- Block on UI detection indefinitely
- Use only template matching (too fragile)
- Ignore error conditions
- Create unbounded retry loops
- Modify state without logging

---

**Status**: ✅ Production Ready
**Maturity**: 85%
