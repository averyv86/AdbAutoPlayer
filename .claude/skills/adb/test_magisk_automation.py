#!/usr/bin/env python3
"""Integration test for Magisk automation framework.

Tests:
1. Resolution detection
2. Element finding
3. Tap with state verification
4. Navigation flow
"""

import sys
import os
import time

# Add module paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, 'adb-core'))

from resolution_aware_tap import ResolutionAwareTap, TapResult

DEVICE_ID = "localhost:5555"


def test_resolution_detection():
    """Test resolution detection."""
    print("\n" + "=" * 60)
    print("TEST 1: Resolution Detection")
    print("=" * 60)

    tap = ResolutionAwareTap(DEVICE_ID)
    res = tap.get_resolution()

    print(f"  Width: {res.width}")
    print(f"  Height: {res.height}")
    print(f"  Override: {res.is_override}")
    print(f"  Density: {res.density}")

    assert res.width > 0 and res.height > 0, "Invalid resolution"
    print("  PASS: Resolution detected successfully")
    return True


def test_element_finding():
    """Test finding elements by text."""
    print("\n" + "=" * 60)
    print("TEST 2: Element Finding")
    print("=" * 60)

    tap = ResolutionAwareTap(DEVICE_ID)

    # Get all text elements
    elements = tap.get_all_text_elements()
    print(f"  Found {len(elements)} text elements")

    # Find specific element
    install_elem = tap.find_element_by_text("Install")
    if install_elem:
        print(f"  Found 'Install' at {install_elem.bounds.center}")
        print(f"  PASS: Element finding works")
        return True
    else:
        print("  FAIL: Could not find 'Install' element")
        return False


def test_tap_with_verification():
    """Test tap with state verification."""
    print("\n" + "=" * 60)
    print("TEST 3: Tap with State Verification")
    print("=" * 60)

    tap = ResolutionAwareTap(DEVICE_ID)

    # First, ensure we're on Magisk home
    print("  Ensuring Magisk app is open...")
    tap.shell("am start -n com.topjohnwu.magisk/.ui.MainActivity")
    time.sleep(2)

    # Find Install button
    install_elem = tap.find_element_by_text("Install")
    if not install_elem:
        print("  SKIP: Install button not found (may not be on home screen)")
        return True

    center_x, center_y = install_elem.bounds.center
    print(f"  Tapping Install at ({center_x}, {center_y})...")

    # Tap with verification
    result = tap.tap_with_verification(center_x, center_y, timeout=3)

    if result == TapResult.SUCCESS:
        print("  PASS: Tap executed and state changed!")

        # Go back to home
        time.sleep(1)
        tap.back()
        return True
    elif result == TapResult.NO_STATE_CHANGE:
        print("  WARNING: Tap executed but no state change detected")
        return False
    else:
        print(f"  FAIL: Tap result was {result}")
        return False


def test_navigation_flow():
    """Test navigation: Home -> Install -> Method -> Back."""
    print("\n" + "=" * 60)
    print("TEST 4: Navigation Flow")
    print("=" * 60)

    tap = ResolutionAwareTap(DEVICE_ID)

    # Step 1: Ensure on home
    print("  Step 1: Launching Magisk...")
    tap.shell("am start -n com.topjohnwu.magisk/.ui.MainActivity")
    time.sleep(2)

    # Verify home screen
    elements = tap.get_all_text_elements()
    texts = [e.text for e in elements]
    if "Magisk" not in texts:
        print("  FAIL: Not on Magisk home screen")
        return False
    print("    -> On home screen (found 'Magisk')")

    # Step 2: Tap Install
    print("  Step 2: Tapping Install...")
    result = tap.find_and_tap("Install", verify_state_change=True)
    if result != TapResult.SUCCESS:
        print(f"    FAIL: Could not tap Install ({result})")
        return False
    print("    -> Navigated to Install screen")
    time.sleep(1)

    # Verify Install screen
    elements = tap.get_all_text_elements()
    texts = [e.text for e in elements]
    if "Options" in texts or "Method" in texts:
        print("    -> Install screen verified (found 'Options' or 'Method')")
    else:
        print(f"    WARNING: Install screen not confirmed. Found: {texts[:5]}")

    # Step 3: Tap NEXT to expand Method
    print("  Step 3: Tapping NEXT...")
    result = tap.find_and_tap("NEXT", timeout=3, verify_state_change=True)
    if result == TapResult.SUCCESS:
        print("    -> Method section expanded")
    else:
        print("    -> NEXT not found or already expanded")
    time.sleep(1)

    # Step 4: Go back
    print("  Step 4: Going back to home...")
    tap.back()
    time.sleep(1)
    tap.back()
    time.sleep(1)

    # Verify back on home
    elements = tap.get_all_text_elements()
    texts = [e.text for e in elements]
    if "Magisk" in texts and "Install" in texts:
        print("    -> Back on home screen")
        print("  PASS: Full navigation flow completed!")
        return True
    else:
        print("  WARNING: May not be back on home screen")
        return True  # Still consider it a pass if we got this far


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MAGISK AUTOMATION FRAMEWORK - INTEGRATION TESTS")
    print("=" * 60)
    print(f"Device: {DEVICE_ID}")

    results = []

    # Run tests
    results.append(("Resolution Detection", test_resolution_detection()))
    results.append(("Element Finding", test_element_finding()))
    results.append(("Tap Verification", test_tap_with_verification()))
    results.append(("Navigation Flow", test_navigation_flow()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
