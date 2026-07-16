#!/usr/bin/env python3
"""Example usage of Magisk Installation Orchestrator.

Demonstrates various usage patterns for the orchestrator including:
- Complete installation
- Resume from specific phase
- Custom configuration
- Error handling

Author: MoAI-ADK
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "adbautoplayer/src-tauri/src-python"))

from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper

# Import orchestrator components
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ui-navigation"))
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ocr-detection"))

from adb_ui_navigator import UINavigator
from adb_ocr_finder import OCRTextFinder
from adb_magisk_orchestrator import MagiskOrchestrator


# ========== EXAMPLE 1: BASIC COMPLETE INSTALLATION ==========

def example_complete_installation():
    """Example: Complete Magisk installation workflow."""
    print("=" * 70)
    print("Example 1: Complete Installation")
    print("=" * 70)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Connect to device
    try:
        device = AdbDeviceWrapper.create_from_settings()
        print(f"✅ Connected to device: {device.serial}")
    except Exception as e:
        print(f"❌ Failed to connect to device: {e}")
        return

    # Create helpers
    ocr_finder = OCRTextFinder(device)
    ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

    # Create orchestrator
    orchestrator = MagiskOrchestrator(
        device=device,
        ui_navigator=ui_navigator,
        ocr_finder=ocr_finder,
        work_dir="/tmp/magisk"
    )

    # Execute installation
    print("\n🚀 Starting installation...")
    result = orchestrator.execute_installation(magisk_version="latest")

    # Display results
    print("\n" + "=" * 70)
    if result.success:
        print("✅ Installation Successful!")
        print(f"   Version: {result.magisk_version}")
        print(f"   Duration: {result.total_duration:.1f}s")
        print(f"   Phases Completed: {len(result.phases)}/7")
    else:
        print("❌ Installation Failed")
        print(f"   Error: {result.error}")
        print("\nPhase Details:")
        for phase in result.phases:
            status = "✅" if phase.success else "❌"
            print(f"   {status} Phase {phase.phase_number}: {phase.phase_name}")
            if not phase.success and phase.error:
                print(f"      Error: {phase.error}")
    print("=" * 70)


# ========== EXAMPLE 2: RESUME FROM SPECIFIC PHASE ==========

def example_resume_from_phase():
    """Example: Resume installation from specific phase."""
    print("=" * 70)
    print("Example 2: Resume from Phase 3 (Skip Download & Install)")
    print("=" * 70)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        device = AdbDeviceWrapper.create_from_settings()
        ocr_finder = OCRTextFinder(device)
        ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

        orchestrator = MagiskOrchestrator(
            device=device,
            ui_navigator=ui_navigator,
            ocr_finder=ocr_finder,
            work_dir="/tmp/magisk"
        )

        # Resume from phase 3 (skip phases 1-2)
        print("⏭️  Skipping phases 1-2 (assuming APK already installed)")
        result = orchestrator.execute_installation(
            magisk_version="30.6",
            skip_phases=[1, 2]
        )

        if result.success:
            print(f"✅ Resume successful! Completed in {result.total_duration:.1f}s")
        else:
            print(f"❌ Resume failed: {result.error}")

    except Exception as e:
        print(f"❌ Error: {e}")


# ========== EXAMPLE 3: CUSTOM CONFIGURATION ==========

def example_custom_configuration():
    """Example: Custom configuration and settings."""
    print("=" * 70)
    print("Example 3: Custom Configuration")
    print("=" * 70)

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        device = AdbDeviceWrapper.create_from_settings()
        ocr_finder = OCRTextFinder(device)
        ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

        # Custom work directory
        custom_work_dir = Path.home() / "Downloads/magisk_install"
        custom_work_dir.mkdir(parents=True, exist_ok=True)

        orchestrator = MagiskOrchestrator(
            device=device,
            ui_navigator=ui_navigator,
            ocr_finder=ocr_finder,
            work_dir=str(custom_work_dir)
        )

        # Configure retry settings
        orchestrator.MAX_RETRIES = 5
        orchestrator.TIMEOUT_DEFAULT = 45

        print(f"📁 Work directory: {custom_work_dir}")
        print(f"🔄 Max retries: {orchestrator.MAX_RETRIES}")
        print(f"⏱️  Timeout: {orchestrator.TIMEOUT_DEFAULT}s")

        result = orchestrator.execute_installation(magisk_version="latest")

        if result.success:
            print(f"\n✅ Installation complete!")
            print(f"   Files saved to: {custom_work_dir}")
        else:
            print(f"\n❌ Installation failed: {result.error}")

    except Exception as e:
        print(f"❌ Error: {e}")


# ========== EXAMPLE 4: DETAILED ERROR HANDLING ==========

def example_error_handling():
    """Example: Comprehensive error handling."""
    print("=" * 70)
    print("Example 4: Comprehensive Error Handling")
    print("=" * 70)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        device = AdbDeviceWrapper.create_from_settings()
    except Exception as e:
        print(f"❌ Device connection failed: {e}")
        print("   Solutions:")
        print("   - Check ADB server is running: adb devices")
        print("   - Verify device is connected via USB or WiFi")
        print("   - Check device authorization in device settings")
        return

    try:
        ocr_finder = OCRTextFinder(device)
        ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

        orchestrator = MagiskOrchestrator(
            device=device,
            ui_navigator=ui_navigator,
            ocr_finder=ocr_finder
        )

        result = orchestrator.execute_installation()

        # Handle different failure scenarios
        if not result.success:
            print(f"\n❌ Installation Failed: {result.error}")

            # Analyze which phase failed
            for phase in result.phases:
                if not phase.success:
                    print(f"\n🔍 Failed Phase: {phase.phase_name}")
                    print(f"   Error: {phase.error}")
                    print(f"   Retry Count: {phase.retry_count}")

                    # Provide specific guidance
                    if phase.phase_number == 1:
                        print("   Solutions:")
                        print("   - Check internet connection")
                        print("   - Verify GitHub access not blocked")
                        print("   - Try specific version instead of 'latest'")
                    elif phase.phase_number == 2:
                        print("   Solutions:")
                        print("   - Check device storage space")
                        print("   - Verify APK download completed")
                        print("   - Try reinstall with --force flag")
                    elif phase.phase_number == 3:
                        print("   Solutions:")
                        print("   - Check device is rooted")
                        print("   - Verify boot partition access")
                        print("   - Check device permissions")
                    elif phase.phase_number == 4:
                        print("   Solutions:")
                        print("   - Verify Magisk app is functional")
                        print("   - Check screen is unlocked")
                        print("   - Increase timeout in config")
                    elif phase.phase_number == 5:
                        print("   Solutions:")
                        print("   - Check bootloader is unlocked")
                        print("   - Verify fastboot connection")
                        print("   - Check fastboot drivers installed")
                    elif phase.phase_number == 6:
                        print("   Solutions:")
                        print("   - Check OCR configuration")
                        print("   - Verify screen resolution compatible")
                        print("   - Try manual verification")
                    elif phase.phase_number == 7:
                        print("   Solutions:")
                        print("   - Check Magisk Settings accessible")
                        print("   - Verify UI navigation working")
                        print("   - Try enabling manually")

                    break
        else:
            print("\n✅ Installation successful!")
            print(f"   Version: {result.magisk_version}")
            print(f"   Duration: {result.total_duration:.1f}s")

    except KeyboardInterrupt:
        print("\n⚠️  Installation interrupted by user")
        print("   To resume, run with skip_phases for completed phases")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("   Check logs for details")


# ========== EXAMPLE 5: PHASE-BY-PHASE MONITORING ==========

def example_phase_monitoring():
    """Example: Monitor each phase individually."""
    print("=" * 70)
    print("Example 5: Phase-by-Phase Monitoring")
    print("=" * 70)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        device = AdbDeviceWrapper.create_from_settings()
        ocr_finder = OCRTextFinder(device)
        ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

        orchestrator = MagiskOrchestrator(
            device=device,
            ui_navigator=ui_navigator,
            ocr_finder=ocr_finder
        )

        print("\n📊 Starting installation with detailed monitoring...\n")

        result = orchestrator.execute_installation()

        # Display detailed phase report
        print("\n" + "=" * 70)
        print("Phase Completion Report")
        print("=" * 70)

        for phase in result.phases:
            status_icon = "✅" if phase.success else "❌"
            print(f"\n{status_icon} Phase {phase.phase_number}: {phase.phase_name}")
            print(f"   Status: {phase.status.value}")
            print(f"   Duration: {phase.duration:.1f}s")
            print(f"   Retries: {phase.retry_count}")

            if phase.data:
                print("   Data:")
                for key, value in phase.data.items():
                    print(f"      {key}: {value}")

            if phase.error:
                print(f"   Error: {phase.error}")

        print("\n" + "=" * 70)
        print(f"Total Duration: {result.total_duration:.1f}s")
        print(f"Overall Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error: {e}")


# ========== MAIN ==========

def main():
    """Run examples."""
    print("\n🎯 Magisk Installation Orchestrator Examples\n")

    examples = [
        ("1", "Complete Installation", example_complete_installation),
        ("2", "Resume from Phase", example_resume_from_phase),
        ("3", "Custom Configuration", example_custom_configuration),
        ("4", "Error Handling", example_error_handling),
        ("5", "Phase Monitoring", example_phase_monitoring),
    ]

    print("Available Examples:")
    for num, name, _ in examples:
        print(f"  {num}. {name}")

    print("\nSelect example (1-5) or 'all' to run all examples:")
    choice = input("> ").strip().lower()

    if choice == "all":
        for _, _, func in examples:
            func()
            print("\n" + "=" * 70 + "\n")
    elif choice in [num for num, _, _ in examples]:
        func = next(func for num, _, func in examples if num == choice)
        func()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
