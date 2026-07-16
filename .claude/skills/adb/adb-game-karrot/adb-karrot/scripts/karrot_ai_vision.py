#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.39.0"]
# ///
"""
Karrot AI Vision - Claude Vision-based Screen Understanding System

This script provides modern AI-powered screen understanding for Karrot app automation.
Instead of brittle template matching or hard-coded coordinates, it uses Claude Vision
to semantically understand the screen and locate UI elements.

Key Features:
- Semantic element detection ("Find the Get Started button")
- Game state recognition (welcome, login, home, etc.)
- Error/popup detection (Play Store, permission dialogs)
- Coordinate extraction from visual analysis
- Smart caching to reduce API calls

Usage:
    uv run karrot_ai_vision.py --analyze /tmp/screenshot.png
    uv run karrot_ai_vision.py --find "Get Started button" --image /tmp/screenshot.png
    uv run karrot_ai_vision.py --state /tmp/screenshot.png
    uv run karrot_ai_vision.py --errors /tmp/screenshot.png
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

try:
    import anthropic
except ImportError:
    print("[ERROR] anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"  # claude-3-5-sonnet is fast and accurate for vision
MAX_TOKENS = 1024
SCREEN_RESOLUTION = (1440, 2560)  # BlueStacks Air resolution

# Cache settings
CACHE_DIR = Path("/tmp/karrot-ai-cache")
CACHE_TTL_SEC = 60  # Cache results for 60 seconds


class GameState(Enum):
    """Karrot app states"""
    UNKNOWN = "unknown"
    SPLASH = "splash"
    WELCOME = "welcome"
    LOGIN = "login"
    PHONE_INPUT = "phone_input"
    VERIFICATION = "verification"
    NEIGHBORHOOD_SELECT = "neighborhood_select"
    HOME = "home"
    SETTINGS = "settings"
    ERROR = "error"
    PLAY_STORE = "play_store"
    PERMISSION_DIALOG = "permission_dialog"


@dataclass
class Point:
    """Screen coordinate"""
    x: int
    y: int

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


@dataclass
class BoundingBox:
    """Element bounding box"""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> Point:
        return Point(
            x=(self.x1 + self.x2) // 2,
            y=(self.y1 + self.y2) // 2
        )

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1


@dataclass
class UIElement:
    """Detected UI element"""
    name: str
    element_type: str  # button, text, input, icon, etc.
    bounds: BoundingBox
    confidence: float  # 0.0 - 1.0
    state: str = "enabled"  # enabled, disabled, highlighted
    text: str = ""

    @property
    def center(self) -> Point:
        return self.bounds.center


@dataclass
class ScreenAnalysis:
    """Complete screen analysis result"""
    timestamp: str
    game_state: GameState
    elements: list[UIElement] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class ErrorInfo:
    """Detected error information"""
    error_type: str  # play_store, permission, network, login_failed, etc.
    description: str
    recovery_action: str  # tap_ok, navigate_back, restart_app, etc.
    bounds: Optional[BoundingBox] = None


class KarrotAIVision:
    """Claude Vision-based screen understanding system"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_analysis: Optional[ScreenAnalysis] = None

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, image_path: str) -> str:
        """Get media type from file extension"""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(ext, "image/png")

    def _call_vision_api(self, image_path: str, prompt: str) -> str:
        """Call Claude Vision API with image and prompt"""
        image_data = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)

        message = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        return message.content[0].text

    def analyze_screen(self, image_path: str) -> ScreenAnalysis:
        """
        Analyze the entire screen and return structured information.
        Returns all UI elements, game state, and any errors detected.
        """
        prompt = f"""Analyze this Karrot (당근마켓) mobile app screenshot.
Screen resolution: {SCREEN_RESOLUTION[0]}x{SCREEN_RESOLUTION[1]}

Provide a JSON response with:
1. "game_state": One of: splash, welcome, login, phone_input, verification, neighborhood_select, home, settings, error, play_store, permission_dialog, unknown
2. "elements": Array of detected UI elements, each with:
   - "name": Descriptive name (e.g., "Get Started button", "Phone input field")
   - "type": button, text, input, icon, link, image
   - "bounds": {{"x1": int, "y1": int, "x2": int, "y2": int}} approximate pixel coordinates
   - "confidence": 0.0-1.0 how confident you are
   - "state": enabled, disabled, highlighted
   - "text": Any text on the element
3. "errors": Array of any error conditions detected (strings)

Focus on interactive elements (buttons, inputs, links).
Return ONLY valid JSON, no markdown or explanation."""

        response = self._call_vision_api(image_path, prompt)

        # Parse JSON response
        try:
            # Clean response - remove markdown if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse JSON response: {e}")
            print(f"[DEBUG] Raw response: {response[:500]}")
            return ScreenAnalysis(
                timestamp=datetime.now().isoformat(),
                game_state=GameState.UNKNOWN,
                raw_response=response
            )

        # Build ScreenAnalysis from response
        elements = []
        for elem in data.get("elements", []):
            bounds = elem.get("bounds", {})
            elements.append(UIElement(
                name=elem.get("name", "Unknown"),
                element_type=elem.get("type", "unknown"),
                bounds=BoundingBox(
                    x1=bounds.get("x1", 0),
                    y1=bounds.get("y1", 0),
                    x2=bounds.get("x2", 0),
                    y2=bounds.get("y2", 0),
                ),
                confidence=elem.get("confidence", 0.5),
                state=elem.get("state", "enabled"),
                text=elem.get("text", ""),
            ))

        state_str = data.get("game_state", "unknown")
        try:
            game_state = GameState(state_str)
        except ValueError:
            game_state = GameState.UNKNOWN

        analysis = ScreenAnalysis(
            timestamp=datetime.now().isoformat(),
            game_state=game_state,
            elements=elements,
            errors=data.get("errors", []),
            raw_response=response,
        )

        self._last_analysis = analysis
        return analysis

    def find_element(self, image_path: str, description: str) -> Optional[Point]:
        """
        Find a specific UI element by semantic description.
        Returns the center point if found, None otherwise.
        """
        prompt = f"""Find the "{description}" in this Karrot app screenshot.
Screen resolution: {SCREEN_RESOLUTION[0]}x{SCREEN_RESOLUTION[1]}

Return ONLY a JSON object with:
- "found": true/false
- "x": center x coordinate (integer)
- "y": center y coordinate (integer)
- "confidence": 0.0-1.0

If not found, set found=false and x=0, y=0.
Return ONLY valid JSON, no explanation."""

        response = self._call_vision_api(image_path, prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            data = json.loads(cleaned)

            if data.get("found", False) and data.get("confidence", 0) > 0.5:
                return Point(x=data.get("x", 0), y=data.get("y", 0))

        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse response: {e}")

        return None

    def get_game_state(self, image_path: str) -> GameState:
        """
        Quickly determine the current game state.
        Uses a simpler prompt for faster response.
        """
        prompt = f"""What screen is shown in this Karrot (당근마켓) app screenshot?

Return ONLY ONE word from this list:
splash, welcome, login, phone_input, verification, neighborhood_select, home, settings, error, play_store, permission_dialog, unknown

No explanation, just the single word."""

        response = self._call_vision_api(image_path, prompt)
        state_str = response.strip().lower()

        try:
            return GameState(state_str)
        except ValueError:
            return GameState.UNKNOWN

    def detect_error(self, image_path: str) -> Optional[ErrorInfo]:
        """
        Detect if there's an error, popup, or unexpected state.
        Returns error info with recovery suggestion.
        """
        prompt = """Check this screenshot for any error conditions, popups, or unexpected states.

Return JSON with:
- "has_error": true/false
- "error_type": play_store, permission, network, login_failed, app_crash, ad_overlay, unknown
- "description": Brief description of the error
- "recovery_action": tap_ok, tap_cancel, navigate_back, restart_app, close_popup, none
- "action_coordinates": {"x": int, "y": int} if there's a button to tap

Return ONLY valid JSON."""

        response = self._call_vision_api(image_path, prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            data = json.loads(cleaned)

            if data.get("has_error", False):
                coords = data.get("action_coordinates", {})
                bounds = None
                if coords.get("x") and coords.get("y"):
                    # Create a small bounding box around the action point
                    x, y = coords["x"], coords["y"]
                    bounds = BoundingBox(x1=x-50, y1=y-30, x2=x+50, y2=y+30)

                return ErrorInfo(
                    error_type=data.get("error_type", "unknown"),
                    description=data.get("description", "Unknown error"),
                    recovery_action=data.get("recovery_action", "none"),
                    bounds=bounds,
                )

        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse error response: {e}")

        return None

    def suggest_action(self, image_path: str, target_state: str) -> dict:
        """
        Suggest the next action to reach the target state.
        Returns action type and coordinates.
        """
        prompt = f"""Analyze this Karrot app screenshot.
Current goal: Navigate to "{target_state}" screen.
Screen resolution: {SCREEN_RESOLUTION[0]}x{SCREEN_RESOLUTION[1]}

What's the next action to take?

Return JSON with:
- "action": tap, swipe, type, wait, back
- "x": x coordinate (for tap)
- "y": y coordinate (for tap)
- "text": text to type (if action is type)
- "direction": up, down, left, right (if action is swipe)
- "reason": Brief explanation

Return ONLY valid JSON."""

        response = self._call_vision_api(image_path, prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            return json.loads(cleaned)

        except json.JSONDecodeError:
            return {"action": "wait", "reason": "Failed to parse response"}


def capture_screenshot(output_path: str = "/tmp/karrot_screen.png") -> str:
    """Capture screenshot from device via ADB"""
    try:
        subprocess.run(
            ["adb", "shell", "screencap", "-p", "/sdcard/screen.png"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["adb", "pull", "/sdcard/screen.png", output_path],
            check=True,
            capture_output=True
        )
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to capture screenshot: {e}")
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Karrot AI Vision - Claude Vision-based Screen Understanding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analyze /tmp/screenshot.png           Full screen analysis
  %(prog)s --find "Get Started button" --image /tmp/screenshot.png
  %(prog)s --state /tmp/screenshot.png             Get current game state
  %(prog)s --errors /tmp/screenshot.png            Check for errors
  %(prog)s --capture                               Capture and analyze
        """
    )

    parser.add_argument(
        "--analyze", "-a",
        metavar="IMAGE",
        help="Analyze screenshot and return all elements"
    )
    parser.add_argument(
        "--find", "-f",
        metavar="DESCRIPTION",
        help="Find element by description (requires --image)"
    )
    parser.add_argument(
        "--image", "-i",
        metavar="PATH",
        help="Image path for --find command"
    )
    parser.add_argument(
        "--state", "-s",
        metavar="IMAGE",
        help="Get game state from screenshot"
    )
    parser.add_argument(
        "--errors", "-e",
        metavar="IMAGE",
        help="Check for errors in screenshot"
    )
    parser.add_argument(
        "--capture", "-c",
        action="store_true",
        help="Capture screenshot from device and analyze"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return 1

    try:
        vision = KarrotAIVision()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 1

    # Handle --capture
    if args.capture:
        print("[CAPTURE] Taking screenshot from device...")
        image_path = capture_screenshot()
        if not image_path:
            return 1
        args.analyze = image_path

    # Handle --analyze
    if args.analyze:
        print(f"[ANALYZE] Analyzing {args.analyze}...")
        start_time = time.time()
        analysis = vision.analyze_screen(args.analyze)
        elapsed = time.time() - start_time

        if args.json:
            output = {
                "timestamp": analysis.timestamp,
                "game_state": analysis.game_state.value,
                "elements": [
                    {
                        "name": e.name,
                        "type": e.element_type,
                        "center": {"x": e.center.x, "y": e.center.y},
                        "confidence": e.confidence,
                        "state": e.state,
                        "text": e.text,
                    }
                    for e in analysis.elements
                ],
                "errors": analysis.errors,
                "elapsed_sec": round(elapsed, 2),
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*50}")
            print(f"SCREEN ANALYSIS (took {elapsed:.2f}s)")
            print(f"{'='*50}")
            print(f"Game State: {analysis.game_state.value}")
            print(f"\nDetected Elements ({len(analysis.elements)}):")
            for elem in analysis.elements:
                print(f"  - {elem.name}")
                print(f"    Type: {elem.element_type}, State: {elem.state}")
                print(f"    Center: ({elem.center.x}, {elem.center.y})")
                print(f"    Confidence: {elem.confidence:.0%}")
                if elem.text:
                    print(f"    Text: {elem.text}")

            if analysis.errors:
                print(f"\nErrors Detected:")
                for error in analysis.errors:
                    print(f"  - {error}")

        return 0

    # Handle --find
    if args.find:
        if not args.image:
            print("[ERROR] --find requires --image")
            return 1

        print(f"[FIND] Looking for '{args.find}'...")
        start_time = time.time()
        point = vision.find_element(args.image, args.find)
        elapsed = time.time() - start_time

        if args.json:
            output = {
                "found": point is not None,
                "x": point.x if point else 0,
                "y": point.y if point else 0,
                "elapsed_sec": round(elapsed, 2),
            }
            print(json.dumps(output, indent=2))
        else:
            if point:
                print(f"[FOUND] '{args.find}' at ({point.x}, {point.y})")
            else:
                print(f"[NOT FOUND] '{args.find}' not detected in image")
            print(f"(took {elapsed:.2f}s)")

        return 0 if point else 1

    # Handle --state
    if args.state:
        print(f"[STATE] Detecting game state...")
        start_time = time.time()
        state = vision.get_game_state(args.state)
        elapsed = time.time() - start_time

        if args.json:
            print(json.dumps({
                "state": state.value,
                "elapsed_sec": round(elapsed, 2)
            }))
        else:
            print(f"Game State: {state.value} (took {elapsed:.2f}s)")

        return 0

    # Handle --errors
    if args.errors:
        print(f"[ERRORS] Checking for errors...")
        start_time = time.time()
        error = vision.detect_error(args.errors)
        elapsed = time.time() - start_time

        if args.json:
            if error:
                output = {
                    "has_error": True,
                    "type": error.error_type,
                    "description": error.description,
                    "recovery_action": error.recovery_action,
                    "elapsed_sec": round(elapsed, 2),
                }
                if error.bounds:
                    output["action_point"] = {
                        "x": error.bounds.center.x,
                        "y": error.bounds.center.y
                    }
            else:
                output = {"has_error": False, "elapsed_sec": round(elapsed, 2)}
            print(json.dumps(output, indent=2))
        else:
            if error:
                print(f"\n{'='*50}")
                print("ERROR DETECTED")
                print(f"{'='*50}")
                print(f"Type: {error.error_type}")
                print(f"Description: {error.description}")
                print(f"Recovery: {error.recovery_action}")
                if error.bounds:
                    print(f"Action Point: ({error.bounds.center.x}, {error.bounds.center.y})")
            else:
                print("[OK] No errors detected")
            print(f"(took {elapsed:.2f}s)")

        return 0

    # No command specified
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
