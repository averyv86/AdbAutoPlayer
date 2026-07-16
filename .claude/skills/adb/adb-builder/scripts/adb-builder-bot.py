#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tomli>=2.0.1",
#     "tomli-w>=1.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
adb-builder-bot: Specialized Meta-Generator for Game Bot Skills

Extends adb-builder-skill with game bot-specific features including state
management, vision automation, recovery patterns, and performance optimization.

Features:
  - Game bot skill scaffolding
  - State machine generation
  - Vision-based element detection templates
  - Recovery rule patterns
  - Performance optimization patterns
  - Multi-phase execution workflows

Usage:
  uv run adb-builder-bot.py \\
    --game "afk-journey" \\
    --bot-type "quest-runner" \\
    --phases "3" \\
    --features "state-tracking,ocr-detection,recovery" \\
    --output-format json
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# Enumerations
# ============================================================================

class GameType(Enum):
    """Supported game types"""
    AFK_JOURNEY = "afk-journey"
    GUITAR_GIRL = "guitar-girl"
    KARROT = "karrot"
    MAGISK = "magisk"


class BotType(Enum):
    """Bot operation types"""
    QUEST_RUNNER = "quest-runner"
    ARENA_FIGHTER = "arena-fighter"
    DUNGEON_CRAWLER = "dungeon-crawler"
    COLLECTOR = "collector"


class Feature(Enum):
    """Bot features"""
    STATE_TRACKING = "state-tracking"
    OCR_DETECTION = "ocr-detection"
    RECOVERY = "recovery"
    PERFORMANCE = "performance"
    LOGGING = "logging"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class BotGenerationParams:
    """Bot generation parameters"""
    game: str
    bot_type: str
    phases: int = 3
    features: List[str] = None
    output_format: str = "json"
    use_skill_generator: bool = True


@dataclass
class BotGenerationReport:
    """Bot generation report"""
    timestamp: str
    bot_name: str
    bot_path: str
    game: str
    bot_type: str
    modules_created: int
    scripts_created: int
    workflows_created: int
    total_lines_generated: int
    success: bool
    messages: List[str]


# ============================================================================
# Template Generator
# ============================================================================

class BotTemplateGenerator:
    """Generates game bot-specific templates"""

    @staticmethod
    def generate_state_manager(game: str, bot_type: str) -> str:
        """Generate state manager module"""
        return f"""# Game State Manager for {game.title()} {bot_type.title()}

## Overview

Manages bot state transitions and progress tracking for {game} {bot_type} automation.

## State Machine

```
IDLE → CHECKING → EXECUTING → VALIDATING → COMPLETED/ERROR → RECOVERY → IDLE
```

## States

### 1. IDLE
Initial state, waiting for trigger.

### 2. CHECKING
Verify current game state and preconditions.

### 3. EXECUTING
Perform main automation actions.

### 4. VALIDATING
Verify execution results.

### 5. COMPLETED
Action completed successfully.

### 6. ERROR
Error occurred during execution.

### 7. RECOVERY
Attempt to recover from error.

## Implementation

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

class StateManager:
    def __init__(self):
        self.current_state = BotState.IDLE
        self.state_entry_time = None
        self.state_timeout = 30

    def transition(self, new_state: BotState):
        \"\"\"Transition to new state\"\"\"
        self.current_state = new_state
        self.state_entry_time = time.time()

    def is_timeout(self) -> bool:
        \"\"\"Check if current state exceeded timeout\"\"\"
        elapsed = time.time() - self.state_entry_time
        return elapsed > self.state_timeout
```

## Progress Tracking

Track progress within each operation:

```python
class ProgressTracker:
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.completed_steps = []

    def advance(self):
        self.current_step += 1
        self.completed_steps.append(self.current_step)

    def get_progress(self) -> float:
        return (len(self.completed_steps) / self.total_steps) * 100
```

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
"""

    @staticmethod
    def generate_vision_automation(game: str) -> str:
        """Generate vision automation module"""
        return f"""# Vision-Based Element Detection for {game.title()}

## Overview

Automated element detection and interaction using template matching and OCR.

## Detection Methods

### 1. Template Matching
Match UI elements using image templates.

```python
class TemplateDetector:
    def __init__(self, template_path: str):
        self.template = cv2.imread(template_path)

    def detect(self, frame) -> Optional[Tuple]:
        \"\"\"Detect template in frame\"\"\"
        result = cv2.matchTemplate(frame, self.template,
                                   cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > 0.8:
            return max_loc
        return None
```

### 2. OCR-Based Detection
Text recognition for dynamic elements.

```python
import pytesseract

class OCRDetector:
    def detect_text(self, region) -> str:
        \"\"\"Extract text from region\"\"\"
        return pytesseract.image_to_string(region)

    def find_text(self, frame, target_text: str) -> Optional[Tuple]:
        \"\"\"Find region containing text\"\"\"
        text = self.detect_text(frame)
        if target_text.lower() in text.lower():
            return self._locate_text(frame, target_text)
        return None
```

### 3. Feature Matching
Detect elements using feature points.

```python
class FeatureDetector:
    def __init__(self):
        self.orb = cv2.ORB_create()

    def detect(self, frame, template):
        \"\"\"Detect using feature points\"\"\"
        kp1, des1 = self.orb.detectAndCompute(frame, None)
        kp2, des2 = self.orb.detectAndCompute(template, None)

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheckb=True)
        matches = bf.match(des1, des2)

        if len(matches) > 10:
            return True
        return False
```

## Preprocessing

Enhance detection accuracy:

```python
class VisionPreprocessor:
    @staticmethod
    def apply_clahe(image):
        \"\"\"Apply CLAHE for contrast enhancement\"\"\"
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        return clahe.apply(image)

    @staticmethod
    def apply_morphology(image):
        \"\"\"Apply morphological operations\"\"\"
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
```

## Interaction

Click detected elements:

```python
class ElementInteractor:
    def __init__(self, device):
        self.device = device

    def click_element(self, location: Tuple[int, int]):
        \"\"\"Click on detected element\"\"\"
        x, y = location
        self.device.tap(x, y)

    def swipe_region(self, start: Tuple, end: Tuple):
        \"\"\"Swipe between regions\"\"\"
        self.device.swipe(start[0], start[1], end[0], end[1])
```

---

**Status**: ✅ Production Ready
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""

    @staticmethod
    def generate_recovery_patterns(bot_type: str) -> str:
        """Generate error recovery patterns"""
        return f"""# Error Recovery Patterns for {bot_type.title()}

## Recovery Strategies

### 1. Retry Strategy
Retry failed operations with exponential backoff.

```python
class RetryStrategy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args, **kwargs):
        \"\"\"Execute function with retry\"\"\"
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
```

### 2. Fallback Chain
Try alternative methods if primary fails.

```python
class FallbackChain:
    def __init__(self, strategies: List[Callable]):
        self.strategies = strategies

    def execute(self, *args, **kwargs):
        \"\"\"Try strategies in order\"\"\"
        for strategy in self.strategies:
            try:
                return strategy(*args, **kwargs)
            except Exception:
                continue
        raise Exception("All fallback strategies failed")
```

### 3. State Reset
Reset to known good state on error.

```python
class StateReset:
    def reset_to_home(self):
        \"\"\"Return to home screen\"\"\"
        self.device.press_home()
        time.sleep(2)

    def force_close_game(self):
        \"\"\"Force close and restart game\"\"\"
        self.device.close_app(self.package_name)
        time.sleep(3)
        self.device.open_app(self.package_name)
```

## Recovery Rules

Define recovery conditions and actions:

```yaml
recovery_rules:
  timeout:
    condition: "state_timeout > 60"
    action: "reset_to_home"
    retry: true

  crash_detection:
    condition: "app_not_responding"
    action: "force_close_game"
    retry: true

  stuck_state:
    condition: "same_state > 5_minutes"
    action: "attempt_recovery"
    retry: true
```

---

**Status**: ✅ Production Ready
"""

    @staticmethod
    def generate_performance_template() -> str:
        """Generate performance optimization template"""
        return """# Performance Optimization Guide

## Profiling

Measure execution time:

```python
import time

class PerfProfiler:
    def profile(self, func, *args, **kwargs):
        \"\"\"Profile function execution\"\"\"
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
```

## Optimization Strategies

### 1. Caching
Cache expensive computations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def detect_element(image_path: str) -> bool:
    # Detection logic
    pass
```

### 2. Parallel Processing
Process multiple tasks concurrently:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(detect, img) for img in images]
    results = [f.result() for f in futures]
```

### 3. Lazy Loading
Defer initialization until needed:

```python
class LazyInitializer:
    def __init__(self):
        self._resource = None

    @property
    def resource(self):
        if self._resource is None:
            self._resource = self._initialize()
        return self._resource
```

## Benchmarking

```python
import timeit

execution_time = timeit.timeit(lambda: my_function(), number=1000)
avg_time = execution_time / 1000
print(f"Average execution time: {avg_time:.2f}ms")
```

---

**Status**: ✅ Production Ready
"""


# ============================================================================
# Bot Generator
# ============================================================================

class AdbBotGenerator:
    """Main bot generation engine"""

    def __init__(self, base_path: Path):
        """Initialize bot generator"""
        self.base_path = base_path
        self.messages: List[str] = []
        self.files_created = 0
        self.scripts_created = 0
        self.workflows_created = 0
        self.total_lines = 0

    def generate(self, params: BotGenerationParams) -> BotGenerationReport:
        """Generate complete game bot skill"""
        bot_name = f"adb-game-{params.game}"
        bot_path = self.base_path / "adb" / bot_name

        try:
            # Create base structure
            self._create_structure(bot_path, params)

            # Generate bot-specific modules
            self._generate_state_manager(bot_path, params)
            self._generate_vision_automation(bot_path, params)
            self._generate_recovery_patterns(bot_path, params)
            self._generate_performance_template(bot_path)

            # Generate bot scripts
            self._generate_bot_scripts(bot_path, params)

            # Generate workflows
            self._generate_workflows(bot_path, params)

            # Generate documentation
            self._generate_documentation(bot_path, params)

            self.messages.append(f"✅ Bot generation complete: {bot_name}")

            return BotGenerationReport(
                timestamp=datetime.now().isoformat(),
                bot_name=bot_name,
                bot_path=str(bot_path),
                game=params.game,
                bot_type=params.bot_type,
                modules_created=4,
                scripts_created=self.scripts_created,
                workflows_created=self.workflows_created,
                total_lines_generated=self.total_lines,
                success=True,
                messages=self.messages
            )

        except Exception as e:
            self.messages.append(f"❌ Error: {str(e)}")
            return BotGenerationReport(
                timestamp=datetime.now().isoformat(),
                bot_name=bot_name,
                bot_path=str(bot_path),
                game=params.game,
                bot_type=params.bot_type,
                modules_created=0,
                scripts_created=0,
                workflows_created=0,
                total_lines_generated=0,
                success=False,
                messages=self.messages
            )

    def _create_structure(self, bot_path: Path, params: BotGenerationParams):
        """Create bot directory structure"""
        directories = [
            bot_path,
            bot_path / "modules",
            bot_path / "scripts",
            bot_path / "workflows",
            bot_path / "tests",
            bot_path / "templates",
            bot_path / "documentation",
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.messages.append(f"✅ Created {len(directories)} bot directories")

    def _generate_state_manager(self, bot_path: Path, params: BotGenerationParams):
        """Generate state manager module"""
        module = BotTemplateGenerator.generate_state_manager(params.game, params.bot_type)
        module_path = bot_path / "modules" / "game-state-manager.md"
        module_path.write_text(module)
        self.files_created += 1
        self.total_lines += len(module.splitlines())
        self.messages.append("✅ Generated state manager module")

    def _generate_vision_automation(self, bot_path: Path, params: BotGenerationParams):
        """Generate vision automation module"""
        module = BotTemplateGenerator.generate_vision_automation(params.game)
        module_path = bot_path / "modules" / "vision-automation.md"
        module_path.write_text(module)
        self.files_created += 1
        self.total_lines += len(module.splitlines())
        self.messages.append("✅ Generated vision automation module")

    def _generate_recovery_patterns(self, bot_path: Path, params: BotGenerationParams):
        """Generate recovery patterns module"""
        module = BotTemplateGenerator.generate_recovery_patterns(params.bot_type)
        module_path = bot_path / "modules" / "recovery-patterns.md"
        module_path.write_text(module)
        self.files_created += 1
        self.total_lines += len(module.splitlines())
        self.messages.append("✅ Generated recovery patterns module")

    def _generate_performance_template(self, bot_path: Path):
        """Generate performance optimization template"""
        module = BotTemplateGenerator.generate_performance_template()
        module_path = bot_path / "modules" / "performance-optimization.md"
        module_path.write_text(module)
        self.files_created += 1
        self.total_lines += len(module.splitlines())
        self.messages.append("✅ Generated performance template")

    def _generate_bot_scripts(self, bot_path: Path, params: BotGenerationParams):
        """Generate bot execution scripts"""
        # Main bot executor
        bot_executor = f"""#!/usr/bin/env python3
# Bot executor for {params.game} {params.bot_type}

def execute_bot():
    \"\"\"Main bot execution loop\"\"\"
    # Initialize
    # Main loop
    pass

if __name__ == "__main__":
    execute_bot()
"""

        executor_path = bot_path / "scripts" / f"execute-{params.game}.py"
        executor_path.write_text(bot_executor)
        executor_path.chmod(0o755)
        self.scripts_created += 1
        self.files_created += 1
        self.messages.append("✅ Generated bot executor script")

    def _generate_workflows(self, bot_path: Path, params: BotGenerationParams):
        """Generate TOON workflows"""
        # Main execution workflow
        workflow = f"""---
skill: adb-game-{params.game}
bot_type: {params.bot_type}
phases: {params.phases}
---

phases:
  initialization:
    description: Initialize bot
    actions:
      - type: setup

  main_execution:
    description: Execute bot automation
    actions:
      - type: execute

  validation:
    description: Validate results
    actions:
      - type: validate

  error_recovery:
    description: Error recovery
    condition: error
    actions:
      - type: recover

  report:
    description: Generate report
    actions:
      - type: report
"""

        workflow_path = bot_path / "workflows" / "execution.toon"
        workflow_path.write_text(workflow)
        self.workflows_created += 1
        self.files_created += 1
        self.messages.append("✅ Generated execution workflow")

    def _generate_documentation(self, bot_path: Path, params: BotGenerationParams):
        """Generate bot documentation"""
        doc = f"""# {params.game.title()} {params.bot_type.title()} Bot

## Overview

Automated bot for {params.game} {params.bot_type} with the following features:

"""
        if params.features:
            doc += "### Features\n"
            for feature in params.features:
                doc += f"- ✅ {feature}\n"

        doc += f"""

## Quick Start

```bash
uv run scripts/execute-{params.game}.py
```

## Configuration

See `SKILL.md` for configuration options.

## Testing

```bash
pytest tests/ -v --cov
```

---

**Status**: 🟡 In Development
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""

        doc_path = bot_path / "documentation" / "README.md"
        doc_path.write_text(doc)
        self.files_created += 1
        self.messages.append("✅ Generated documentation")


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ADB Game Bot Generator - Create specialized game bot skills"
    )
    parser.add_argument("--game", required=True, help="Game name")
    parser.add_argument("--bot-type", required=True, help="Bot type")
    parser.add_argument("--phases", type=int, default=3, help="Execution phases")
    parser.add_argument("--features", default="", help="Features (comma-separated)")
    parser.add_argument("--output-format", default="json", help="Output format")
    parser.add_argument("--output-path", default=".", help="Base output path")

    args = parser.parse_args()

    params = BotGenerationParams(
        game=args.game,
        bot_type=args.bot_type,
        phases=args.phases,
        features=[f.strip() for f in args.features.split(",") if f.strip()],
        output_format=args.output_format
    )

    # Generate bot
    base_path = Path(args.output_path) / "skills"
    generator = AdbBotGenerator(base_path)
    report = generator.generate(params)

    # Output report
    if args.output_format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(f"Bot for {params.game} generated successfully!")
        print(f"Type: {params.bot_type}")
        print(f"Files created: {report.modules_created + report.scripts_created + report.workflows_created}")
        print(f"Status: {'✅ Success' if report.success else '❌ Failed'}")

    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    main()
