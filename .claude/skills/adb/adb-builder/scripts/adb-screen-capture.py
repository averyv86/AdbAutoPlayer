#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pillow>=9.0.0",
#     "pytesseract>=0.3.10",
# ]
# ///
"""
adb-screen-capture: Screen Capture & OCR Analysis Utility

TRUST 5 Principles:
  1. Transparency - Clear preview and analysis reporting
  2. Reliability - Robust image processing with error recovery
  3. Usability - Simple capture and analysis interface
  4. Security - Safe file handling and permissions
  5. Testability - Detailed analysis output for verification

Provides unified interface for:
  - Screen capture from Android devices
  - Image analysis and OCR
  - Element detection and highlighting
  - Comparative screenshots
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CaptureResult:
    """Screen capture result"""
    device: str
    filepath: str
    timestamp: str
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: int = 0
    success: bool = True
    message: str = ""


class ScreenCapture:
    """Unified screen capture and analysis"""

    def __init__(self, device: str = None):
        self.device = device
        self.errors: List[str] = []

    def capture_screen(self, output_path: str = None, compress: bool = False) -> CaptureResult:
        """Capture screen from Android device"""
        try:
            # Generate output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"screen_{timestamp}.png"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Capture via adb
            adb_cmd = ["adb"]
            if self.device:
                adb_cmd.extend(["-s", self.device])

            adb_cmd.extend(["shell", "screencap", "-p", "/sdcard/screen.png"])

            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Screen capture failed: {result.stderr}")

            # Pull image from device
            pull_cmd = ["adb"]
            if self.device:
                pull_cmd.extend(["-s", self.device])

            pull_cmd.extend(["pull", "/sdcard/screen.png", str(output_path)])

            result = subprocess.run(
                pull_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Image pull failed: {result.stderr}")

            # Get image info
            try:
                from PIL import Image
                img = Image.open(output_path)
                width, height = img.size
            except:
                width, height = None, None

            size_bytes = output_path.stat().st_size if output_path.exists() else 0

            return CaptureResult(
                device=self.device or "default",
                filepath=str(output_path),
                timestamp=datetime.now().isoformat(),
                width=width,
                height=height,
                size_bytes=size_bytes,
                success=True,
                message="Screen captured successfully"
            )

        except Exception as e:
            self.errors.append(str(e))
            return CaptureResult(
                device=self.device or "default",
                filepath=output_path or "",
                timestamp=datetime.now().isoformat(),
                success=False,
                message=str(e)
            )

    def extract_text(self, image_path: str) -> Dict[str, str]:
        """Extract text from screen image via OCR"""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

            return {
                "success": True,
                "text": text,
                "character_count": len(text),
                "line_count": len(text.split('\n'))
            }

        except ImportError:
            return {
                "success": False,
                "error": "tesseract not installed",
                "message": "Install: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "OCR extraction failed"
            }

    def find_elements(self, image_path: str, patterns: List[str]) -> Dict[str, List]:
        """Find UI elements in screen image"""
        results = {"patterns_found": {}, "patterns_not_found": []}

        try:
            text_result = self.extract_text(image_path)
            if not text_result.get("success"):
                return {"error": text_result.get("error")}

            screen_text = text_result.get("text", "")

            for pattern in patterns:
                if pattern.lower() in screen_text.lower():
                    results["patterns_found"][pattern] = True
                else:
                    results["patterns_not_found"].append(pattern)

            return results

        except Exception as e:
            return {"error": str(e)}

    def compare_screens(self, image1_path: str, image2_path: str) -> Dict:
        """Compare two screen captures"""
        try:
            from PIL import Image, ImageChops

            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)

            # Check if sizes match
            if img1.size != img2.size:
                return {
                    "match": False,
                    "reason": "Different dimensions",
                    "dimensions": {
                        "image1": img1.size,
                        "image2": img2.size
                    }
                }

            # Calculate difference
            diff = ImageChops.difference(img1, img2)
            if diff.getbbox() is None:
                return {"match": True, "identical": True}
            else:
                return {
                    "match": False,
                    "identical": False,
                    "differences_detected": True
                }

        except Exception as e:
            return {"error": str(e)}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: adb-screen-capture.py [capture|extract|find|compare]")
        return 1

    command = sys.argv[1]
    device = None

    # Parse device argument if present
    if "--device" in sys.argv:
        idx = sys.argv.index("--device")
        if idx + 1 < len(sys.argv):
            device = sys.argv[idx + 1]

    capture = ScreenCapture(device=device)

    if command == "capture":
        output = sys.argv[2] if len(sys.argv) > 2 else None
        result = capture.capture_screen(output)

        print(f"\n📸 Screen Capture Result:")
        print(f"  Device: {result.device}")
        print(f"  File: {result.filepath}")
        print(f"  Size: {result.width}x{result.height}" if result.width else "  Size: N/A")
        print(f"  Bytes: {result.size_bytes}")
        print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
        if not result.success:
            print(f"  Error: {result.message}")
            return 1

    elif command == "extract":
        if len(sys.argv) < 3:
            print("Usage: adb-screen-capture.py extract <image_path>")
            return 1

        image_path = sys.argv[2]
        result = capture.extract_text(image_path)

        print(f"\n📝 OCR Text Extraction:")
        print(f"  Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
        if result.get("success"):
            print(f"  Characters: {result.get('character_count')}")
            print(f"  Lines: {result.get('line_count')}")
            print(f"\n{result.get('text')}")
        else:
            print(f"  Error: {result.get('error')}")

    elif command == "find":
        if len(sys.argv) < 4:
            print("Usage: adb-screen-capture.py find <image_path> <pattern1> [pattern2] ...")
            return 1

        image_path = sys.argv[2]
        patterns = sys.argv[3:]
        result = capture.find_elements(image_path, patterns)

        print(f"\n🔍 Element Detection:")
        print(f"  Image: {image_path}")
        print(f"  Patterns searched: {len(patterns)}")
        if "patterns_found" in result:
            print(f"  Found: {len(result.get('patterns_found', {}))}")
            for pattern in result.get('patterns_found', {}):
                print(f"    ✅ {pattern}")
            for pattern in result.get('patterns_not_found', []):
                print(f"    ❌ {pattern}")

    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: adb-screen-capture.py compare <image1> <image2>")
            return 1

        image1 = sys.argv[2]
        image2 = sys.argv[3]
        result = capture.compare_screens(image1, image2)

        print(f"\n🔄 Screen Comparison:")
        if result.get("match"):
            print(f"  Result: ✅ Screens match")
            if result.get("identical"):
                print(f"  Status: Identical")
        else:
            print(f"  Result: ❌ Screens differ")
            if result.get("reason"):
                print(f"  Reason: {result.get('reason')}")

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
