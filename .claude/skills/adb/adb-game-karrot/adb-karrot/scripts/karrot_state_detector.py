#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "Pillow>=10.0.0"]
# ///
"""
Karrot State Detector - TOON-based state detection system
Detects current screen state using package detection, OCR, and optional AI vision
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    from PIL import Image
except ImportError:
    print("ERROR: Required dependencies not installed", file=sys.stderr)
    print("Run: uv add pyyaml Pillow", file=sys.stderr)
    sys.exit(1)


class DetectionMethod(Enum):
    """Detection method types"""
    PACKAGE = "package"
    OCR = "ocr"
    PACKAGE_OCR = "package+ocr"
    AI_VISION = "ai_vision"
    UNKNOWN = "unknown"


@dataclass
class OCRRegion:
    """OCR detection region"""
    x: int
    y: int
    w: int
    h: int


@dataclass
class Element:
    """UI element with coordinates"""
    name: str
    x: int
    y: int
    description: str
    tap_variance: int = 5


@dataclass
class StateIndicators:
    """State detection indicators"""
    text: list[str]
    ocr_regions: list[OCRRegion]
    package: Optional[str] = None
    package_not: Optional[list[str]] = None
    package_any: Optional[list[str]] = None


@dataclass
class StateDefinition:
    """Complete state definition from TOON"""
    id: str
    description: str
    indicators: StateIndicators
    elements: dict[str, Element]
    next_states: list[str]
    timeout_sec: int = 30
    is_goal: bool = False


@dataclass
class DetectionResult:
    """State detection result"""
    state: str
    confidence: float
    method: DetectionMethod
    elements: dict[str, dict[str, int]]
    timestamp: str
    raw_data: Optional[dict[str, Any]] = None


class TOONParser:
    """Parse TOON configuration file"""

    def __init__(self, toon_path: Path):
        self.toon_path = toon_path
        self._config: Optional[dict] = None
        self._states: Optional[dict[str, StateDefinition]] = None
        self._banned_zones: Optional[list[dict]] = None

    def _load_config(self) -> dict:
        """Load and cache TOON config"""
        if self._config is None:
            if not self.toon_path.exists():
                raise FileNotFoundError(f"TOON file not found: {self.toon_path}")

            with open(self.toon_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

        return self._config

    def parse_states(self) -> dict[str, StateDefinition]:
        """Parse all state definitions"""
        if self._states is not None:
            return self._states

        config = self._load_config()
        states_raw = config.get('states', {})

        self._states = {}
        for state_id, state_data in states_raw.items():
            # Parse indicators
            indicators_raw = state_data.get('indicators', {})
            ocr_regions = [
                OCRRegion(**region)
                for region in indicators_raw.get('ocr_regions', [])
            ]

            indicators = StateIndicators(
                text=indicators_raw.get('text', []),
                ocr_regions=ocr_regions,
                package=indicators_raw.get('package'),
                package_not=indicators_raw.get('package_not'),
                package_any=indicators_raw.get('package_any')
            )

            # Parse elements
            elements_raw = state_data.get('elements', {})
            elements = {}
            for elem_name, elem_data in elements_raw.items():
                elements[elem_name] = Element(
                    name=elem_name,
                    x=elem_data['x'],
                    y=elem_data['y'],
                    description=elem_data.get('description', ''),
                    tap_variance=elem_data.get('tap_variance', 5)
                )

            self._states[state_id] = StateDefinition(
                id=state_id,
                description=state_data.get('description', ''),
                indicators=indicators,
                elements=elements,
                next_states=state_data.get('next_states', []),
                timeout_sec=state_data.get('timeout_sec', 30),
                is_goal=state_data.get('is_goal', False)
            )

        return self._states

    def get_banned_zones(self) -> list[dict]:
        """Get banned zones configuration"""
        if self._banned_zones is not None:
            return self._banned_zones

        config = self._load_config()
        zones_raw = config.get('banned_zones', {})

        self._banned_zones = []
        for zone_name, zone_data in zones_raw.items():
            self._banned_zones.append({
                'name': zone_name,
                'description': zone_data.get('description', ''),
                'x_min': zone_data['x_min'],
                'x_max': zone_data['x_max'],
                'y_min': zone_data['y_min'],
                'y_max': zone_data['y_max']
            })

        return self._banned_zones

    def get_meta(self) -> dict:
        """Get metadata from TOON"""
        config = self._load_config()
        return config.get('meta', {})


class ADBHelper:
    """ADB command helper with fallbacks"""

    @staticmethod
    def run_command(cmd: list[str], timeout: int = 5) -> tuple[str, int]:
        """Run ADB command with timeout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", -1
        except Exception as e:
            print(f"Command failed: {e}", file=sys.stderr)
            return "", -1

    @classmethod
    def get_current_package(cls) -> Optional[str]:
        """Detect current package with multiple fallback methods"""

        # Method 1: mResumedActivity (most reliable)
        stdout, code = cls.run_command([
            'adb', 'shell',
            'dumpsys', 'activity', 'activities', '|', 'grep', 'mResumedActivity'
        ])
        if code == 0 and stdout:
            # Parse: mResumedActivity: ActivityRecord{...} com.towneers.www/...
            if '/' in stdout:
                parts = stdout.split()
                for part in parts:
                    if '/' in part:
                        package = part.split('/')[0]
                        if '.' in package:  # Valid package format
                            return package

        # Method 2: mCurrentFocus (fallback)
        stdout, code = cls.run_command([
            'adb', 'shell',
            'dumpsys', 'window', '|', 'grep', 'mCurrentFocus'
        ])
        if code == 0 and stdout:
            # Parse: mCurrentFocus=Window{...} com.towneers.www/...
            if ' ' in stdout:
                parts = stdout.split()
                for part in parts:
                    if '/' in part:
                        package = part.split('/')[0]
                        if '.' in package:
                            return package

        # Method 3: windows list (last resort)
        stdout, code = cls.run_command([
            'adb', 'shell',
            'dumpsys', 'window', 'windows'
        ])
        if code == 0 and stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Window #' in line and 'package=' in line:
                    if 'package=' in line:
                        package = line.split('package=')[1].split()[0]
                        if '.' in package:
                            return package

        return None

    @classmethod
    def take_screenshot(cls, output_path: Path) -> bool:
        """Take screenshot via ADB"""
        temp_path = "/sdcard/screenshot.png"

        # Take screenshot on device
        _, code1 = cls.run_command([
            'adb', 'shell', 'screencap', '-p', temp_path
        ], timeout=10)

        if code1 != 0:
            return False

        # Pull to local
        _, code2 = cls.run_command([
            'adb', 'pull', temp_path, str(output_path)
        ], timeout=10)

        # Cleanup
        cls.run_command(['adb', 'shell', 'rm', temp_path])

        return code2 == 0 and output_path.exists()


class OCRDetector:
    """OCR-based state detection (placeholder for pytesseract)"""

    @staticmethod
    def extract_text_from_region(
        image_path: Path,
        region: OCRRegion
    ) -> list[str]:
        """
        Extract text from image region using OCR

        NOTE: This is a placeholder implementation
        For production, install pytesseract: uv add pytesseract
        """
        try:
            # Load image
            img = Image.open(image_path)

            # Crop region
            cropped = img.crop((
                region.x,
                region.y,
                region.x + region.w,
                region.y + region.h
            ))

            # TODO: Implement actual OCR
            # For now, return empty list (package detection will be primary)
            # Real implementation:
            # import pytesseract
            # text = pytesseract.image_to_string(cropped)
            # return [line.strip() for line in text.split('\n') if line.strip()]

            return []

        except Exception as e:
            print(f"OCR extraction failed: {e}", file=sys.stderr)
            return []

    @classmethod
    def detect_text_indicators(
        cls,
        image_path: Path,
        indicators: StateIndicators
    ) -> tuple[float, list[str]]:
        """
        Check if text indicators are present in OCR regions
        Returns: (confidence_score, matched_texts)
        """
        if not indicators.ocr_regions or not indicators.text:
            return 0.0, []

        all_extracted_text = []
        for region in indicators.ocr_regions:
            extracted = cls.extract_text_from_region(image_path, region)
            all_extracted_text.extend(extracted)

        # Match against expected text indicators
        matched = []
        for indicator in indicators.text:
            for extracted in all_extracted_text:
                if indicator.lower() in extracted.lower():
                    matched.append(indicator)
                    break

        if not indicators.text:
            return 0.0, []

        confidence = len(matched) / len(indicators.text)
        return confidence, matched


class StateDetector:
    """Main state detection engine"""

    def __init__(self, toon_path: Path):
        self.parser = TOONParser(toon_path)
        self.states = self.parser.parse_states()
        self.banned_zones = self.parser.get_banned_zones()
        self.meta = self.parser.get_meta()

        # Detection threshold
        self.confidence_threshold = 0.5

    def detect_current_state(
        self,
        screenshot_path: Optional[Path] = None
    ) -> DetectionResult:
        """
        Detect current state using package + OCR + AI vision fallback

        Priority:
        1. Package detection (fast)
        2. OCR detection (if package matches)
        3. AI vision fallback (if enabled and unknown)
        """

        # Phase 1: Package detection
        current_package = ADBHelper.get_current_package()

        if not current_package:
            return DetectionResult(
                state="unknown",
                confidence=0.0,
                method=DetectionMethod.UNKNOWN,
                elements={},
                timestamp=self._get_timestamp(),
                raw_data={"error": "Failed to detect package"}
            )

        # Check if app crashed (package_not/package_any logic)
        crashed_state = self._check_crashed_state(current_package)
        if crashed_state:
            return crashed_state

        # Phase 2: Filter states by package
        package_matched_states = self._filter_by_package(current_package)

        if not package_matched_states:
            # No states match this package
            return DetectionResult(
                state="unknown",
                confidence=0.0,
                method=DetectionMethod.PACKAGE,
                elements={},
                timestamp=self._get_timestamp(),
                raw_data={"package": current_package}
            )

        # Phase 3: OCR detection (if screenshot provided or taken)
        if screenshot_path is None:
            screenshot_path = Path("/tmp/karrot_current.png")
            if not ADBHelper.take_screenshot(screenshot_path):
                # Fall back to package-only detection
                return self._best_package_match(
                    package_matched_states,
                    current_package
                )

        # Phase 4: Score states by OCR + package
        best_state = self._score_states_with_ocr(
            package_matched_states,
            screenshot_path
        )

        return best_state

    def _check_crashed_state(self, current_package: str) -> Optional[DetectionResult]:
        """Check if app is in crashed state"""
        crashed_def = self.states.get('crashed')
        if not crashed_def:
            return None

        indicators = crashed_def.indicators

        # Check package_not (should NOT be in these packages)
        if indicators.package_not:
            target_package = self.meta.get('app_package', 'com.towneers.www')
            if current_package != target_package:
                # App is not running
                return DetectionResult(
                    state="crashed",
                    confidence=1.0,
                    method=DetectionMethod.PACKAGE,
                    elements=self._extract_elements(crashed_def),
                    timestamp=self._get_timestamp(),
                    raw_data={"current_package": current_package}
                )

        return None

    def _filter_by_package(self, current_package: str) -> list[StateDefinition]:
        """Filter states that match current package"""
        matched = []

        for state_def in self.states.values():
            indicators = state_def.indicators

            # Skip crashed/unknown states
            if state_def.id in ('crashed', 'unknown'):
                continue

            # If state specifies package, check match
            if indicators.package:
                if indicators.package == current_package:
                    matched.append(state_def)
            else:
                # State doesn't specify package (assume app package)
                target_package = self.meta.get('app_package')
                if current_package == target_package:
                    matched.append(state_def)

        return matched

    def _best_package_match(
        self,
        states: list[StateDefinition],
        current_package: str
    ) -> DetectionResult:
        """Return best match based on package only"""
        if len(states) == 1:
            state_def = states[0]
            return DetectionResult(
                state=state_def.id,
                confidence=0.6,  # Package-only confidence
                method=DetectionMethod.PACKAGE,
                elements=self._extract_elements(state_def),
                timestamp=self._get_timestamp(),
                raw_data={"package": current_package}
            )

        # Multiple states match - return first (need OCR to disambiguate)
        return DetectionResult(
            state=states[0].id,
            confidence=0.4,
            method=DetectionMethod.PACKAGE,
            elements=self._extract_elements(states[0]),
            timestamp=self._get_timestamp(),
            raw_data={
                "package": current_package,
                "ambiguous": [s.id for s in states]
            }
        )

    def _score_states_with_ocr(
        self,
        states: list[StateDefinition],
        screenshot_path: Path
    ) -> DetectionResult:
        """Score states using OCR detection"""

        best_state = None
        best_score = 0.0
        best_matched_texts = []

        for state_def in states:
            # Package match = 0.5 base score
            score = 0.5
            matched_texts = []

            # OCR detection
            if state_def.indicators.ocr_regions and state_def.indicators.text:
                ocr_confidence, matched = OCRDetector.detect_text_indicators(
                    screenshot_path,
                    state_def.indicators
                )
                score += ocr_confidence * 0.5  # OCR contributes up to 0.5
                matched_texts = matched

            if score > best_score:
                best_score = score
                best_state = state_def
                best_matched_texts = matched_texts

        if best_state is None or best_score < self.confidence_threshold:
            return DetectionResult(
                state="unknown",
                confidence=best_score,
                method=DetectionMethod.PACKAGE_OCR,
                elements={},
                timestamp=self._get_timestamp(),
                raw_data={
                    "best_score": best_score,
                    "threshold": self.confidence_threshold
                }
            )

        return DetectionResult(
            state=best_state.id,
            confidence=best_score,
            method=DetectionMethod.PACKAGE_OCR,
            elements=self._extract_elements(best_state),
            timestamp=self._get_timestamp(),
            raw_data={
                "matched_texts": best_matched_texts,
                "ocr_enabled": len(best_state.indicators.ocr_regions) > 0
            }
        )

    def _extract_elements(self, state_def: StateDefinition) -> dict[str, dict[str, int]]:
        """Extract element coordinates, checking banned zones"""
        elements = {}

        for elem_name, elem in state_def.elements.items():
            # Check if element is in banned zone
            if not self._is_in_banned_zone(elem.x, elem.y):
                elements[elem_name] = {
                    'x': elem.x,
                    'y': elem.y,
                    'tap_variance': elem.tap_variance
                }

        return elements

    def _is_in_banned_zone(self, x: int, y: int) -> bool:
        """Check if coordinate is in any banned zone"""
        for zone in self.banned_zones:
            if (zone['x_min'] <= x <= zone['x_max'] and
                zone['y_min'] <= y <= zone['y_max']):
                return True
        return False

    @staticmethod
    def _get_timestamp() -> str:
        """Get ISO timestamp"""
        return datetime.now().isoformat()

    def get_element_coordinates(
        self,
        state_id: str,
        element_name: str
    ) -> Optional[dict[str, int]]:
        """Get specific element coordinates from state"""
        state_def = self.states.get(state_id)
        if not state_def:
            return None

        elem = state_def.elements.get(element_name)
        if not elem:
            return None

        # Check banned zones
        if self._is_in_banned_zone(elem.x, elem.y):
            return None

        return {
            'x': elem.x,
            'y': elem.y,
            'tap_variance': elem.tap_variance,
            'description': elem.description
        }

    def list_all_states(self) -> list[dict]:
        """List all state definitions"""
        return [
            {
                'id': state_def.id,
                'description': state_def.description,
                'elements': list(state_def.elements.keys()),
                'next_states': state_def.next_states,
                'is_goal': state_def.is_goal
            }
            for state_def in self.states.values()
        ]

    def validate_toon_config(self) -> dict:
        """Validate TOON configuration"""
        errors = []
        warnings = []

        # Check meta
        meta = self.meta
        if not meta.get('app_package'):
            errors.append("Missing meta.app_package")

        # Check states
        for state_id, state_def in self.states.items():
            if not state_def.indicators.text and not state_def.indicators.package:
                warnings.append(f"State '{state_id}' has no detection indicators")

            if not state_def.elements:
                warnings.append(f"State '{state_id}' has no elements defined")

            # Check next_states references
            for next_state in state_def.next_states:
                if next_state not in self.states:
                    errors.append(f"State '{state_id}' references unknown next_state '{next_state}'")

        # Check banned zones
        for zone in self.banned_zones:
            if zone['x_min'] >= zone['x_max']:
                errors.append(f"Invalid banned zone: x_min >= x_max")
            if zone['y_min'] >= zone['y_max']:
                errors.append(f"Invalid banned zone: y_min >= y_max")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'states_count': len(self.states),
            'banned_zones_count': len(self.banned_zones)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Karrot State Detector - TOON-based state detection"
    )

    parser.add_argument(
        '--detect',
        action='store_true',
        help='Detect current state'
    )
    parser.add_argument(
        '--screenshot',
        action='store_true',
        help='Take screenshot and detect state'
    )
    parser.add_argument(
        '--element',
        type=str,
        help='Get coordinates for specific element (requires --state)'
    )
    parser.add_argument(
        '--state',
        type=str,
        help='State ID for element lookup'
    )
    parser.add_argument(
        '--list-states',
        action='store_true',
        help='List all available states'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate TOON configuration'
    )
    parser.add_argument(
        '--toon',
        type=Path,
        help='Path to TOON config file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    args = parser.parse_args()

    # Find TOON config
    if args.toon:
        toon_path = args.toon
    else:
        # Default: ../config/karrot_states.toon
        script_dir = Path(__file__).parent
        toon_path = script_dir.parent / 'config' / 'karrot_states.toon'

    if not toon_path.exists():
        print(f"ERROR: TOON file not found: {toon_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize detector
    try:
        detector = StateDetector(toon_path)
    except Exception as e:
        print(f"ERROR: Failed to initialize detector: {e}", file=sys.stderr)
        sys.exit(1)

    # Execute command
    if args.validate:
        validation = detector.validate_toon_config()
        if args.json:
            print(json.dumps(validation, indent=2))
        else:
            status = "✓ VALID" if validation['valid'] else "✗ INVALID"
            print(f"TOON Validation: {status}")
            print(f"States: {validation['states_count']}")
            print(f"Banned Zones: {validation['banned_zones_count']}")

            if validation['errors']:
                print("\nErrors:")
                for error in validation['errors']:
                    print(f"  - {error}")

            if validation['warnings']:
                print("\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")

        sys.exit(0 if validation['valid'] else 1)

    elif args.list_states:
        states = detector.list_all_states()
        if args.json:
            print(json.dumps(states, indent=2))
        else:
            print(f"Available States ({len(states)}):")
            for state in states:
                goal_mark = " [GOAL]" if state['is_goal'] else ""
                print(f"\n  {state['id']}{goal_mark}")
                print(f"    Description: {state['description']}")
                print(f"    Elements: {', '.join(state['elements'])}")
                if state['next_states']:
                    print(f"    Next States: {', '.join(state['next_states'])}")

        sys.exit(0)

    elif args.element:
        if not args.state:
            print("ERROR: --element requires --state", file=sys.stderr)
            sys.exit(1)

        coords = detector.get_element_coordinates(args.state, args.element)
        if coords is None:
            print(f"ERROR: Element '{args.element}' not found in state '{args.state}'", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(coords, indent=2))
        else:
            print(f"Element: {args.element}")
            print(f"  Position: ({coords['x']}, {coords['y']})")
            print(f"  Variance: ±{coords['tap_variance']}px")
            print(f"  Description: {coords['description']}")

        sys.exit(0)

    elif args.screenshot or args.detect:
        screenshot_path = None
        if args.screenshot:
            screenshot_path = Path("/tmp/karrot_current.png")
            print("Taking screenshot...", file=sys.stderr)
            if not ADBHelper.take_screenshot(screenshot_path):
                print("ERROR: Screenshot failed", file=sys.stderr)
                sys.exit(1)

        print("Detecting state...", file=sys.stderr)
        result = detector.detect_current_state(screenshot_path)

        if args.json:
            output = {
                'state': result.state,
                'confidence': result.confidence,
                'method': result.method.value,
                'elements': result.elements,
                'timestamp': result.timestamp
            }
            if result.raw_data:
                output['raw_data'] = result.raw_data

            print(json.dumps(output, indent=2))
        else:
            print(f"\nDetected State: {result.state}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"Method: {result.method.value}")
            print(f"Timestamp: {result.timestamp}")

            if result.elements:
                print(f"\nAvailable Elements ({len(result.elements)}):")
                for elem_name, coords in result.elements.items():
                    print(f"  {elem_name}: ({coords['x']}, {coords['y']}) ±{coords['tap_variance']}px")

            if result.raw_data:
                print(f"\nRaw Data: {json.dumps(result.raw_data, indent=2)}")

        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
