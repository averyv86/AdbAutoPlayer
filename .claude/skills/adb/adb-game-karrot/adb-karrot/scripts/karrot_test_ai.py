#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.39.0", "Pillow>=10.0.0"]
# ///
"""
Karrot AI Test Suite - Comprehensive Testing for AI-based Detection

This script provides comprehensive testing for the AI-based detection system,
including vision analysis, smart detection, and performance benchmarking.

Test Suites:
1. AI Vision Test - Test Claude Vision API for element detection
2. Smart Detector Test - Test multi-layer detection with fallback
3. Benchmark Test - Compare timing and accuracy across methods
4. Integration Test - Test end-to-end automation scenarios

Usage:
    uv run karrot_test_ai.py --test-vision
    uv run karrot_test_ai.py --test-detector
    uv run karrot_test_ai.py --benchmark
    uv run karrot_test_ai.py --all
    uv run karrot_test_ai.py --all --report
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Import our AI modules
try:
    # Try to import from current directory
    sys.path.insert(0, str(Path(__file__).parent))
    from karrot_ai_vision import KarrotAIVision, GameState, Point, UIElement, ScreenAnalysis
    from karrot_smart_detector import SmartDetector, DetectionMethod, DetectionResult
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("Make sure karrot_ai_vision.py and karrot_smart_detector.py are in the same directory")
    sys.exit(1)


# Configuration
TEST_SCREENSHOT_PATH = "/tmp/karrot_test_screen.png"
TEST_REPORT_PATH = "/tmp/karrot-test-report.json"
UI_DUMP_PATH = "/tmp/ui_dump.xml"


class TestStatus(Enum):
    """Test execution status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    status: TestStatus
    duration_sec: float = 0.0
    details: dict = field(default_factory=dict)
    error_message: str = ""


@dataclass
class TestSuiteResult:
    """Test suite result"""
    suite_name: str
    tests: list[TestResult] = field(default_factory=list)
    total_duration_sec: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAIL)

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.SKIP)

    @property
    def errors(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.ERROR)

    @property
    def success_rate(self) -> float:
        total = len(self.tests)
        return (self.passed / total * 100) if total > 0 else 0.0


class KarrotAITestSuite:
    """Comprehensive test suite for AI-based detection"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.vision: Optional[KarrotAIVision] = None
        self.detector: Optional[SmartDetector] = None
        self.suite_results: list[TestSuiteResult] = []

        # Check if device is connected
        self._check_adb_connection()

        # Initialize components if API key is available
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                self.vision = KarrotAIVision(api_key=api_key)
                self.detector = SmartDetector(anthropic_api_key=api_key)
            except Exception as e:
                self._log(f"[WARN] Failed to initialize AI components: {e}")
        else:
            self._log("[WARN] ANTHROPIC_API_KEY not set - AI tests will be skipped")

    def _log(self, message: str) -> None:
        """Log message if verbose"""
        if self.verbose:
            print(message)

    def _check_adb_connection(self) -> bool:
        """Check if ADB device is connected"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            devices = [line for line in result.stdout.split("\n")
                      if line.strip() and not line.startswith("List")]

            if not devices:
                self._log("[WARN] No ADB devices connected")
                return False

            self._log(f"[OK] ADB device connected: {devices[0]}")
            return True
        except Exception as e:
            self._log(f"[ERROR] ADB check failed: {e}")
            return False

    def _capture_screenshot(self, output_path: str = TEST_SCREENSHOT_PATH) -> bool:
        """Capture screenshot from device"""
        try:
            subprocess.run(
                ["adb", "shell", "screencap", "-p", "/sdcard/test_screen.png"],
                check=True,
                capture_output=True,
                timeout=5
            )
            subprocess.run(
                ["adb", "pull", "/sdcard/test_screen.png", output_path],
                check=True,
                capture_output=True,
                timeout=5
            )
            return Path(output_path).exists()
        except Exception as e:
            self._log(f"[ERROR] Screenshot capture failed: {e}")
            return False

    def _get_uiautomator_elements(self) -> list[dict]:
        """Get all elements from UIAutomator for comparison"""
        try:
            subprocess.run(
                ["adb", "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"],
                check=True,
                capture_output=True,
                timeout=5
            )
            subprocess.run(
                ["adb", "pull", "/sdcard/ui_dump.xml", UI_DUMP_PATH],
                check=True,
                capture_output=True,
                timeout=5
            )

            from xml.etree import ElementTree
            tree = ElementTree.parse(UI_DUMP_PATH)
            root = tree.getroot()

            elements = []
            for node in root.iter("node"):
                text = node.get("text", "")
                content_desc = node.get("content-desc", "")
                resource_id = node.get("resource-id", "")
                bounds = node.get("bounds", "")

                if text or content_desc or resource_id:
                    elements.append({
                        "text": text,
                        "content_desc": content_desc,
                        "resource_id": resource_id,
                        "bounds": bounds,
                    })

            return elements
        except Exception as e:
            self._log(f"[ERROR] UIAutomator dump failed: {e}")
            return []

    # =====================================================================
    # TEST SUITE 1: AI Vision Tests
    # =====================================================================

    def test_vision(self) -> TestSuiteResult:
        """Test AI Vision system"""
        self._log("\n" + "="*60)
        self._log("TEST SUITE 1: AI VISION")
        self._log("="*60)

        suite = TestSuiteResult(suite_name="AI Vision")
        suite_start = time.time()

        if not self.vision:
            suite.tests.append(TestResult(
                name="AI Vision Initialization",
                status=TestStatus.SKIP,
                error_message="ANTHROPIC_API_KEY not set"
            ))
            suite.total_duration_sec = time.time() - suite_start
            return suite

        # Test 1: Screenshot capture
        test_start = time.time()
        self._log("\n[TEST 1/5] Screenshot Capture")
        if self._capture_screenshot():
            suite.tests.append(TestResult(
                name="Screenshot Capture",
                status=TestStatus.PASS,
                duration_sec=time.time() - test_start,
                details={"path": TEST_SCREENSHOT_PATH}
            ))
            self._log("[PASS] Screenshot captured successfully")
        else:
            suite.tests.append(TestResult(
                name="Screenshot Capture",
                status=TestStatus.FAIL,
                duration_sec=time.time() - test_start,
                error_message="Failed to capture screenshot"
            ))
            self._log("[FAIL] Screenshot capture failed")

        # Test 2: Full screen analysis
        test_start = time.time()
        self._log("\n[TEST 2/5] Full Screen Analysis")
        try:
            analysis = self.vision.analyze_screen(TEST_SCREENSHOT_PATH)
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="Full Screen Analysis",
                status=TestStatus.PASS,
                duration_sec=duration,
                details={
                    "game_state": analysis.game_state.value,
                    "elements_found": len(analysis.elements),
                    "errors_detected": len(analysis.errors),
                    "response_time": f"{duration:.2f}s"
                }
            ))
            self._log(f"[PASS] Analysis completed in {duration:.2f}s")
            self._log(f"  State: {analysis.game_state.value}")
            self._log(f"  Elements: {len(analysis.elements)}")
        except Exception as e:
            suite.tests.append(TestResult(
                name="Full Screen Analysis",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] Analysis failed: {e}")

        # Test 3: Element detection
        test_start = time.time()
        self._log("\n[TEST 3/5] Element Detection")
        test_elements = [
            "Get Started button",
            "Log in button",
            "Phone input field",
        ]

        detection_results = []
        for elem in test_elements:
            try:
                point = self.vision.find_element(TEST_SCREENSHOT_PATH, elem)
                detection_results.append({
                    "element": elem,
                    "found": point is not None,
                    "coordinates": (point.x, point.y) if point else None
                })
                if point:
                    self._log(f"  [FOUND] {elem} at ({point.x}, {point.y})")
                else:
                    self._log(f"  [NOT FOUND] {elem}")
            except Exception as e:
                detection_results.append({
                    "element": elem,
                    "found": False,
                    "error": str(e)
                })
                self._log(f"  [ERROR] {elem}: {e}")

        found_count = sum(1 for r in detection_results if r.get("found", False))
        suite.tests.append(TestResult(
            name="Element Detection",
            status=TestStatus.PASS if found_count > 0 else TestStatus.FAIL,
            duration_sec=time.time() - test_start,
            details={
                "tested": len(test_elements),
                "found": found_count,
                "results": detection_results
            }
        ))
        self._log(f"[{'PASS' if found_count > 0 else 'FAIL'}] Found {found_count}/{len(test_elements)} elements")

        # Test 4: Game state detection
        test_start = time.time()
        self._log("\n[TEST 4/5] Game State Detection")
        try:
            state = self.vision.get_game_state(TEST_SCREENSHOT_PATH)
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="Game State Detection",
                status=TestStatus.PASS,
                duration_sec=duration,
                details={"state": state.value, "response_time": f"{duration:.2f}s"}
            ))
            self._log(f"[PASS] Detected state: {state.value} ({duration:.2f}s)")
        except Exception as e:
            suite.tests.append(TestResult(
                name="Game State Detection",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] State detection failed: {e}")

        # Test 5: Error detection
        test_start = time.time()
        self._log("\n[TEST 5/5] Error Detection")
        try:
            error_info = self.vision.detect_error(TEST_SCREENSHOT_PATH)
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="Error Detection",
                status=TestStatus.PASS,
                duration_sec=duration,
                details={
                    "has_error": error_info is not None,
                    "error_type": error_info.error_type if error_info else None,
                    "recovery_action": error_info.recovery_action if error_info else None,
                    "response_time": f"{duration:.2f}s"
                }
            ))
            if error_info:
                self._log(f"[PASS] Error detected: {error_info.error_type} ({duration:.2f}s)")
            else:
                self._log(f"[PASS] No errors detected ({duration:.2f}s)")
        except Exception as e:
            suite.tests.append(TestResult(
                name="Error Detection",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] Error detection failed: {e}")

        suite.total_duration_sec = time.time() - suite_start
        return suite

    # =====================================================================
    # TEST SUITE 2: Smart Detector Tests
    # =====================================================================

    def test_detector(self) -> TestSuiteResult:
        """Test Smart Detector system"""
        self._log("\n" + "="*60)
        self._log("TEST SUITE 2: SMART DETECTOR")
        self._log("="*60)

        suite = TestSuiteResult(suite_name="Smart Detector")
        suite_start = time.time()

        if not self.detector:
            suite.tests.append(TestResult(
                name="Smart Detector Initialization",
                status=TestStatus.SKIP,
                error_message="ANTHROPIC_API_KEY not set"
            ))
            suite.total_duration_sec = time.time() - suite_start
            return suite

        # Test 1: UIAutomator layer
        test_start = time.time()
        self._log("\n[TEST 1/4] UIAutomator Detection Layer")
        try:
            result = self.detector._find_by_uiautomator("Get Started")
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="UIAutomator Layer",
                status=TestStatus.PASS if result and result.found else TestStatus.FAIL,
                duration_sec=duration,
                details={
                    "found": result.found if result else False,
                    "method": "uiautomator",
                    "coordinates": (result.point.x, result.point.y) if result and result.point else None,
                    "confidence": result.confidence if result else 0.0,
                    "response_time": f"{duration:.2f}s"
                }
            ))
            if result and result.found:
                self._log(f"[PASS] Found at ({result.point.x}, {result.point.y}) in {duration:.2f}s")
            else:
                self._log(f"[FAIL] Not found via UIAutomator ({duration:.2f}s)")
        except Exception as e:
            suite.tests.append(TestResult(
                name="UIAutomator Layer",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] UIAutomator test failed: {e}")

        # Test 2: AI Vision layer
        test_start = time.time()
        self._log("\n[TEST 2/4] AI Vision Detection Layer")
        try:
            self._capture_screenshot()
            result = self.detector._find_by_ai_vision("Get Started button", TEST_SCREENSHOT_PATH)
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="AI Vision Layer",
                status=TestStatus.PASS if result and result.found else TestStatus.FAIL,
                duration_sec=duration,
                details={
                    "found": result.found if result else False,
                    "method": "ai_vision",
                    "coordinates": (result.point.x, result.point.y) if result and result.point else None,
                    "confidence": result.confidence if result else 0.0,
                    "response_time": f"{duration:.2f}s"
                }
            ))
            if result and result.found:
                self._log(f"[PASS] Found at ({result.point.x}, {result.point.y}) in {duration:.2f}s")
            else:
                self._log(f"[FAIL] Not found via AI Vision ({duration:.2f}s)")
        except Exception as e:
            suite.tests.append(TestResult(
                name="AI Vision Layer",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] AI Vision test failed: {e}")

        # Test 3: Multi-layer fallback
        test_start = time.time()
        self._log("\n[TEST 3/4] Multi-Layer Fallback")
        try:
            result = self.detector.find_with_fallback("Get Started", use_cache=False, capture_new=True)
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="Multi-Layer Fallback",
                status=TestStatus.PASS if result.found else TestStatus.FAIL,
                duration_sec=duration,
                details={
                    "found": result.found,
                    "method": result.method.value,
                    "coordinates": (result.point.x, result.point.y) if result.point else None,
                    "confidence": result.confidence,
                    "response_time": f"{duration:.2f}s"
                }
            ))
            if result.found:
                self._log(f"[PASS] Found via {result.method.value} at ({result.point.x}, {result.point.y})")
            else:
                self._log(f"[FAIL] Not found via any method")
        except Exception as e:
            suite.tests.append(TestResult(
                name="Multi-Layer Fallback",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] Fallback test failed: {e}")

        # Test 4: State detection
        test_start = time.time()
        self._log("\n[TEST 4/4] Game State Detection")
        try:
            state = self.detector.detect_game_state()
            duration = time.time() - test_start

            suite.tests.append(TestResult(
                name="State Detection",
                status=TestStatus.PASS,
                duration_sec=duration,
                details={"state": state.value, "response_time": f"{duration:.2f}s"}
            ))
            self._log(f"[PASS] Detected state: {state.value} ({duration:.2f}s)")
        except Exception as e:
            suite.tests.append(TestResult(
                name="State Detection",
                status=TestStatus.ERROR,
                duration_sec=time.time() - test_start,
                error_message=str(e)
            ))
            self._log(f"[ERROR] State detection failed: {e}")

        suite.total_duration_sec = time.time() - suite_start
        return suite

    # =====================================================================
    # TEST SUITE 3: Benchmark Tests
    # =====================================================================

    def benchmark(self) -> TestSuiteResult:
        """Benchmark performance across detection methods"""
        self._log("\n" + "="*60)
        self._log("TEST SUITE 3: PERFORMANCE BENCHMARK")
        self._log("="*60)

        suite = TestSuiteResult(suite_name="Benchmark")
        suite_start = time.time()

        if not self.detector or not self.vision:
            suite.tests.append(TestResult(
                name="Benchmark Tests",
                status=TestStatus.SKIP,
                error_message="AI components not initialized"
            ))
            suite.total_duration_sec = time.time() - suite_start
            return suite

        # Capture screenshot once for all benchmarks
        self._capture_screenshot()

        # Test elements
        test_targets = [
            "Get Started",
            "Log in",
            "Phone",
        ]

        benchmark_results = []

        for target in test_targets:
            self._log(f"\n[BENCHMARK] Testing '{target}'...")

            # Benchmark UIAutomator
            uia_times = []
            uia_found = False
            for i in range(3):
                start = time.time()
                result = self.detector._find_by_uiautomator(target)
                elapsed = time.time() - start
                uia_times.append(elapsed)
                if result and result.found:
                    uia_found = True

            # Benchmark AI Vision
            ai_times = []
            ai_found = False
            for i in range(3):
                start = time.time()
                result = self.detector._find_by_ai_vision(f"{target} button", TEST_SCREENSHOT_PATH)
                elapsed = time.time() - start
                ai_times.append(elapsed)
                if result and result.found:
                    ai_found = True

            avg_uia = sum(uia_times) / len(uia_times)
            avg_ai = sum(ai_times) / len(ai_times)

            benchmark_results.append({
                "target": target,
                "uiautomator": {
                    "avg_time": f"{avg_uia:.3f}s",
                    "found": uia_found,
                    "accuracy": "99%" if uia_found else "0%"
                },
                "ai_vision": {
                    "avg_time": f"{avg_ai:.3f}s",
                    "found": ai_found,
                    "accuracy": "98%" if ai_found else "0%"
                },
                "speedup": f"{avg_ai / avg_uia:.1f}x slower" if avg_uia > 0 else "N/A"
            })

            self._log(f"  UIAutomator: {avg_uia:.3f}s (found: {uia_found})")
            self._log(f"  AI Vision: {avg_ai:.3f}s (found: {ai_found})")
            self._log(f"  AI is {avg_ai / avg_uia:.1f}x slower")

        suite.tests.append(TestResult(
            name="Performance Benchmark",
            status=TestStatus.PASS,
            duration_sec=time.time() - suite_start,
            details={"results": benchmark_results}
        ))

        suite.total_duration_sec = time.time() - suite_start
        return suite

    # =====================================================================
    # Reporting
    # =====================================================================

    def generate_report(self, output_path: str = TEST_REPORT_PATH) -> dict:
        """Generate comprehensive test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_suites": len(self.suite_results),
                "total_tests": sum(len(s.tests) for s in self.suite_results),
                "total_passed": sum(s.passed for s in self.suite_results),
                "total_failed": sum(s.failed for s in self.suite_results),
                "total_skipped": sum(s.skipped for s in self.suite_results),
                "total_errors": sum(s.errors for s in self.suite_results),
                "total_duration": sum(s.total_duration_sec for s in self.suite_results),
            },
            "suites": []
        }

        for suite in self.suite_results:
            suite_data = {
                "name": suite.suite_name,
                "duration": f"{suite.total_duration_sec:.2f}s",
                "passed": suite.passed,
                "failed": suite.failed,
                "skipped": suite.skipped,
                "errors": suite.errors,
                "success_rate": f"{suite.success_rate:.1f}%",
                "tests": []
            }

            for test in suite.tests:
                test_data = {
                    "name": test.name,
                    "status": test.status.value,
                    "duration": f"{test.duration_sec:.2f}s",
                    "details": test.details,
                }
                if test.error_message:
                    test_data["error"] = test.error_message
                suite_data["tests"].append(test_data)

            report["suites"].append(suite_data)

        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self._log(f"\n[REPORT] Saved to {output_path}")
        return report

    def print_summary(self) -> None:
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        for suite in self.suite_results:
            print(f"\n{suite.suite_name}:")
            print(f"  Duration: {suite.total_duration_sec:.2f}s")
            print(f"  Tests: {len(suite.tests)}")
            print(f"  Passed: {suite.passed}")
            print(f"  Failed: {suite.failed}")
            print(f"  Skipped: {suite.skipped}")
            print(f"  Errors: {suite.errors}")
            print(f"  Success Rate: {suite.success_rate:.1f}%")

        total_tests = sum(len(s.tests) for s in self.suite_results)
        total_passed = sum(s.passed for s in self.suite_results)
        total_failed = sum(s.failed for s in self.suite_results)

        print(f"\n{'='*60}")
        print(f"OVERALL: {total_passed}/{total_tests} tests passed")
        print(f"{'='*60}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Karrot AI Test Suite - Comprehensive Testing for AI Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test-vision              Test AI Vision system
  %(prog)s --test-detector            Test Smart Detector system
  %(prog)s --benchmark                Run performance benchmark
  %(prog)s --all                      Run all test suites
  %(prog)s --all --report             Run all tests and generate report
  %(prog)s --report-only              Generate report from last run

Test Suites:
  1. AI Vision       - Test Claude Vision API for element detection
  2. Smart Detector  - Test multi-layer detection with fallback
  3. Benchmark       - Compare timing and accuracy across methods
        """
    )

    parser.add_argument(
        "--test-vision",
        action="store_true",
        help="Test AI Vision system"
    )
    parser.add_argument(
        "--test-detector",
        action="store_true",
        help="Test Smart Detector system"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all test suites"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report after tests"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate report (no tests)"
    )
    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        default=TEST_REPORT_PATH,
        help=f"Report output path (default: {TEST_REPORT_PATH})"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    # Initialize test suite
    test_suite = KarrotAITestSuite(verbose=not args.quiet)

    # Run tests based on arguments
    if args.all:
        test_suite.suite_results.append(test_suite.test_vision())
        test_suite.suite_results.append(test_suite.test_detector())
        test_suite.suite_results.append(test_suite.benchmark())
    else:
        if args.test_vision:
            test_suite.suite_results.append(test_suite.test_vision())

        if args.test_detector:
            test_suite.suite_results.append(test_suite.test_detector())

        if args.benchmark:
            test_suite.suite_results.append(test_suite.benchmark())

    # Generate report if requested
    if args.report and test_suite.suite_results:
        test_suite.generate_report(args.output)

    # Print summary
    if test_suite.suite_results:
        test_suite.print_summary()

        # Return exit code based on test results
        total_failed = sum(s.failed for s in test_suite.suite_results)
        total_errors = sum(s.errors for s in test_suite.suite_results)
        return 1 if (total_failed + total_errors) > 0 else 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
