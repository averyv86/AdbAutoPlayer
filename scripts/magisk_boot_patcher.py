#!/usr/bin/env python3
"""Magisk Boot Image Patcher.

This script automates the process of patching an Android boot.img
using Magisk for gaining root access.

Two methods supported:
1. Using Magisk app on device (RECOMMENDED - handles all complexities)
2. Manual patching with magiskboot (ADVANCED - requires all Magisk components)

Usage:
    # Method 1: Use Magisk app (recommended)
    python magisk_boot_patcher.py --boot boot.img --method app

    # Method 2: Manual patching (advanced)
    python magisk_boot_patcher.py --boot boot.img --method manual --magiskboot ./magiskboot

Requirements:
    - ADB access to Android device
    - Magisk app installed on device (for method 1)
    - magiskboot binary (for method 2)
    - boot.img matching device firmware
"""

import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class MagiskBootPatcher:
    """Automate Magisk boot image patching."""

    def __init__(self, boot_img_path: Path, output_dir: Path):
        """Initialize patcher.

        Args:
            boot_img_path: Path to original boot.img
            output_dir: Directory for output files
        """
        self.boot_img_path = boot_img_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Verify boot.img exists
        if not self.boot_img_path.exists():
            raise FileNotFoundError(f"boot.img not found: {self.boot_img_path}")

    def verify_boot_img(self) -> bool:
        """Verify boot.img is valid Android boot image.

        Returns:
            True if valid boot image
        """
        print("Verifying boot.img...")

        # Check file signature (should start with "ANDROID!")
        with open(self.boot_img_path, "rb") as f:
            header = f.read(8)
            if header != b"ANDROID!":
                print(f"ERROR: Invalid boot image header: {header}")
                return False

        # Check file size (typically 32-96 MB)
        size_mb = self.boot_img_path.stat().st_size / (1024 * 1024)
        print(f"Boot image size: {size_mb:.2f} MB")

        if size_mb < 10 or size_mb > 200:
            print(f"WARNING: Unusual boot image size: {size_mb:.2f} MB")
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != "y":
                return False

        # Calculate SHA256 for verification
        sha256 = self._calculate_sha256(self.boot_img_path)
        print(f"Boot image SHA256: {sha256}")

        # Save hash for later verification
        hash_file = self.output_dir / "boot_original.sha256"
        hash_file.write_text(f"{sha256}  {self.boot_img_path.name}\n")

        print("Boot image verification: OK")
        return True

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def check_adb_connection(self) -> bool:
        """Verify ADB connection to device.

        Returns:
            True if device is connected
        """
        print("Checking ADB connection...")

        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                check=True,
            )

            devices = [
                line
                for line in result.stdout.split("\n")
                if "\tdevice" in line
            ]

            if not devices:
                print("ERROR: No ADB devices found")
                print("Connect your device and enable USB debugging")
                return False

            device_id = devices[0].split("\t")[0]
            print(f"Connected to device: {device_id}")

            # Get device info
            model = subprocess.run(
                ["adb", "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            android_version = subprocess.run(
                ["adb", "shell", "getprop", "ro.build.version.release"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            print(f"Device: {model}")
            print(f"Android version: {android_version}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"ERROR: ADB command failed: {e}")
            return False
        except FileNotFoundError:
            print("ERROR: ADB not found. Install Android Platform Tools")
            return False

    def patch_with_magisk_app(self) -> Optional[Path]:
        """Patch boot.img using Magisk app on device.

        This is the RECOMMENDED method as the Magisk app handles all
        complexities of patching including ramdisk injection, compression,
        and signing.

        Returns:
            Path to patched boot image, or None if failed
        """
        print("\n" + "=" * 60)
        print("METHOD 1: Patching with Magisk App")
        print("=" * 60)

        # Check if Magisk is installed
        print("\nChecking for Magisk app...")
        try:
            result = subprocess.run(
                ["adb", "shell", "pm", "list", "packages", "com.topjohnwu.magisk"],
                capture_output=True,
                text=True,
                check=True,
            )

            if "com.topjohnwu.magisk" not in result.stdout:
                print("ERROR: Magisk app not installed on device")
                print("Install Magisk from: https://github.com/topjohnwu/Magisk/releases")
                return None

            print("Magisk app found: OK")

        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to check for Magisk: {e}")
            return None

        # Push boot.img to device
        device_boot_path = "/sdcard/Download/boot_to_patch.img"
        print(f"\nPushing boot.img to device: {device_boot_path}")

        try:
            subprocess.run(
                ["adb", "push", str(self.boot_img_path), device_boot_path],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to push boot.img: {e}")
            return None

        # Instructions for manual patching via Magisk app
        print("\n" + "=" * 60)
        print("MANUAL STEP REQUIRED")
        print("=" * 60)
        print("\nOn your Android device:")
        print("1. Open Magisk Manager app")
        print("2. Tap 'Install' next to Magisk")
        print("3. Select 'Select and Patch a File'")
        print(f"4. Navigate to: {device_boot_path}")
        print("5. Wait for patching to complete")
        print("6. Note the output filename (e.g., magisk_patched_xxxxx.img)")
        print("\nPress ENTER when patching is complete...")
        input()

        # Try to find patched boot image
        print("\nSearching for patched boot image...")

        try:
            result = subprocess.run(
                ["adb", "shell", "ls", "-t", "/sdcard/Download/magisk_patched*.img"],
                capture_output=True,
                text=True,
                check=True,
            )

            patched_files = result.stdout.strip().split("\n")
            if not patched_files or not patched_files[0]:
                print("ERROR: No patched boot image found")
                print("Expected location: /sdcard/Download/magisk_patched_*.img")
                return None

            # Use most recent file
            device_patched_path = patched_files[0].strip()
            print(f"Found patched boot: {device_patched_path}")

            # Pull patched boot image
            local_patched_path = self.output_dir / "magisk_patched.img"
            print(f"Pulling patched boot to: {local_patched_path}")

            subprocess.run(
                ["adb", "pull", device_patched_path, str(local_patched_path)],
                check=True,
            )

            # Verify patched image
            if not local_patched_path.exists():
                print("ERROR: Failed to pull patched boot image")
                return None

            patched_size_mb = local_patched_path.stat().st_size / (1024 * 1024)
            print(f"Patched boot size: {patched_size_mb:.2f} MB")

            # Calculate hash
            patched_sha256 = self._calculate_sha256(local_patched_path)
            print(f"Patched boot SHA256: {patched_sha256}")

            # Save hash
            hash_file = self.output_dir / "magisk_patched.sha256"
            hash_file.write_text(f"{patched_sha256}  {local_patched_path.name}\n")

            print("\n" + "=" * 60)
            print("SUCCESS! Boot image patched")
            print("=" * 60)
            print(f"\nPatched boot: {local_patched_path.absolute()}")

            return local_patched_path

        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to find/pull patched boot: {e}")
            return None

    def patch_with_magiskboot(self, magiskboot_path: Path) -> Optional[Path]:
        """Patch boot.img using magiskboot binary.

        WARNING: This is an INCOMPLETE implementation. Full Magisk patching
        requires additional components:
        - magisk32/magisk64 binaries
        - magiskinit
        - Magisk stub APK
        - Various scripts and configurations

        This method is provided for educational purposes but is NOT
        recommended for actual use. Use patch_with_magisk_app() instead.

        Args:
            magiskboot_path: Path to magiskboot binary

        Returns:
            Path to patched boot image, or None if failed
        """
        print("\n" + "=" * 60)
        print("METHOD 2: Manual Patching with magiskboot")
        print("=" * 60)
        print("\nWARNING: This is an ADVANCED method requiring all Magisk components")
        print("For production use, METHOD 1 (Magisk app) is STRONGLY recommended\n")

        if not magiskboot_path.exists():
            print(f"ERROR: magiskboot not found: {magiskboot_path}")
            return None

        # Create work directory
        work_dir = self.output_dir / "magiskboot_work"
        work_dir.mkdir(exist_ok=True)

        print(f"Work directory: {work_dir}")

        # Copy boot.img to work directory
        work_boot = work_dir / "boot.img"
        print(f"Copying boot.img to work directory...")

        import shutil
        shutil.copy2(self.boot_img_path, work_boot)

        try:
            # Step 1: Unpack boot image
            print("\nUnpacking boot.img...")
            result = subprocess.run(
                [str(magiskboot_path), "unpack", "boot.img"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            print(result.stdout)

            # List unpacked files
            unpacked_files = list(work_dir.glob("*"))
            print(f"\nUnpacked files:")
            for f in unpacked_files:
                if f.is_file():
                    size_kb = f.stat().st_size / 1024
                    print(f"  - {f.name} ({size_kb:.1f} KB)")

            # Step 2: This is where Magisk would modify the ramdisk
            # We CANNOT do this without full Magisk components
            print("\n" + "=" * 60)
            print("INCOMPLETE: Ramdisk Modification Required")
            print("=" * 60)
            print("\nTo complete patching, you need:")
            print("1. magisk32 or magisk64 binary")
            print("2. magiskinit binary")
            print("3. Magisk stub APK")
            print("4. init.magisk.rc script")
            print("5. Policy patches")
            print("\nThese must be injected into the ramdisk before repacking.")
            print("\nFor now, we'll demonstrate unpacking/repacking without modifications:")

            # Step 3: Repack boot image (without modifications - just demonstration)
            print("\nRepacking boot.img (UNMODIFIED - demonstration only)...")
            result = subprocess.run(
                [str(magiskboot_path), "repack", "boot.img"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            print(result.stdout)

            # Find repacked image
            repacked_img = work_dir / "new-boot.img"
            if not repacked_img.exists():
                print("ERROR: Repacking failed - new-boot.img not found")
                return None

            # Move to output
            output_img = self.output_dir / "boot_repacked_unmodified.img"
            shutil.move(str(repacked_img), str(output_img))

            print("\n" + "=" * 60)
            print("DEMONSTRATION COMPLETE")
            print("=" * 60)
            print(f"\nRepacked (unmodified) boot: {output_img.absolute()}")
            print("\nWARNING: This boot image is NOT patched with Magisk!")
            print("It was only unpacked and repacked for demonstration.")
            print("\nUse METHOD 1 (--method app) for actual Magisk patching.")

            return output_img

        except subprocess.CalledProcessError as e:
            print(f"ERROR: magiskboot command failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None

    def generate_flash_instructions(self, patched_boot: Path):
        """Generate instructions for flashing patched boot image.

        Args:
            patched_boot: Path to patched boot image
        """
        instructions_file = self.output_dir / "FLASH_INSTRUCTIONS.txt"

        instructions = f"""
{'=' * 70}
MAGISK PATCHED BOOT IMAGE - FLASHING INSTRUCTIONS
{'=' * 70}

Patched Boot Image: {patched_boot.absolute()}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 70}
CRITICAL WARNINGS
{'=' * 70}

⚠️  BOOTLOADER MUST BE UNLOCKED
⚠️  WRONG BOOT IMAGE CAN BRICK YOUR DEVICE
⚠️  SAMSUNG DEVICES: KNOX WILL BE TRIPPED (IRREVERSIBLE)
⚠️  BACKUP YOUR DATA BEFORE PROCEEDING
⚠️  OTA UPDATES WILL FAIL AFTER ROOTING

{'=' * 70}
METHOD 1: Fastboot (RECOMMENDED)
{'=' * 70}

1. Boot device into fastboot mode:
   - Power off device
   - Hold Volume Down + Power button
   - Or: adb reboot bootloader

2. Verify fastboot connection:
   fastboot devices

3. Flash patched boot image:
   fastboot flash boot {patched_boot.absolute()}

4. Reboot device:
   fastboot reboot

{'=' * 70}
METHOD 2: TWRP Recovery (If Installed)
{'=' * 70}

1. Boot into TWRP recovery
2. Select "Install"
3. Select "Install Image"
4. Navigate to: {patched_boot.absolute()}
5. Select "Boot" partition
6. Swipe to confirm
7. Reboot system

{'=' * 70}
METHOD 3: Samsung Odin (Samsung Devices Only)
{'=' * 70}

1. Download Odin: https://odindownload.com/
2. Boot device into Download Mode:
   - Power off device
   - Hold Volume Down + Power + Bixby button

3. In Odin:
   - Click "AP" button
   - Select patched boot image
   - Check "Auto Reboot"
   - Click "Start"

Note: For Samsung, you may need to pack boot.img into AP tar format

{'=' * 70}
VERIFICATION AFTER FLASHING
{'=' * 70}

1. Device should boot normally (may show bootloader warning)

2. Open Magisk Manager app:
   - Should show "Installed: v27.x" (or current version)
   - If not, reinstall Magisk app

3. Test root access:
   adb shell
   su
   # Should get root prompt (#)

4. Install Root Checker app from Play Store to verify

{'=' * 70}
TROUBLESHOOTING
{'=' * 70}

Boot Loop:
- Boot into recovery
- Flash original boot.img
- Or perform factory reset

Magisk Not Working:
- Reinstall Magisk Manager APK
- Clear Magisk app data
- Reflash patched boot

SafetyNet Fails:
- Install Magisk Hide Props Config module
- Enable Magisk Hide for banking apps
- Use Universal SafetyNet Fix module

{'=' * 70}
BACKUP FILES (SAVE THESE!)
{'=' * 70}

Original boot.img:     {self.boot_img_path.absolute()}
Patched boot.img:      {patched_boot.absolute()}
Original SHA256:       {self.output_dir / 'boot_original.sha256'}
Patched SHA256:        {self.output_dir / 'magisk_patched.sha256'}

Store these in a safe location for recovery!

{'=' * 70}
ADDITIONAL RESOURCES
{'=' * 70}

Magisk Documentation: https://topjohnwu.github.io/Magisk/
XDA Forums:           https://forum.xda-developers.com/
Magisk GitHub:        https://github.com/topjohnwu/Magisk

{'=' * 70}
        """

        instructions_file.write_text(instructions)
        print(f"\nFlashing instructions saved to: {instructions_file.absolute()}")
        print("\nREAD THE INSTRUCTIONS CAREFULLY BEFORE FLASHING!")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Magisk Boot Image Patcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Patch using Magisk app (recommended)
  python magisk_boot_patcher.py --boot boot.img --method app

  # Manual patching with magiskboot (advanced)
  python magisk_boot_patcher.py --boot boot.img --method manual --magiskboot ./magiskboot

  # Specify custom output directory
  python magisk_boot_patcher.py --boot boot.img --output ./patched/ --method app
        """,
    )

    parser.add_argument(
        "--boot",
        "-b",
        type=Path,
        required=True,
        help="Path to original boot.img",
    )

    parser.add_argument(
        "--method",
        "-m",
        choices=["app", "manual"],
        default="app",
        help="Patching method: 'app' (Magisk app - recommended) or 'manual' (magiskboot)",
    )

    parser.add_argument(
        "--magiskboot",
        type=Path,
        help="Path to magiskboot binary (required for manual method)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./magisk_patched"),
        help="Output directory (default: ./magisk_patched)",
    )

    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip boot.img verification checks",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.method == "manual" and not args.magiskboot:
        print("ERROR: --magiskboot required for manual method", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize patcher
        patcher = MagiskBootPatcher(args.boot, args.output)

        # Verify boot image
        if not args.skip_verification:
            if not patcher.verify_boot_img():
                print("Boot image verification failed", file=sys.stderr)
                sys.exit(1)

        # Check ADB connection
        if not patcher.check_adb_connection():
            print("ADB connection required", file=sys.stderr)
            sys.exit(1)

        # Perform patching based on method
        patched_boot = None

        if args.method == "app":
            patched_boot = patcher.patch_with_magisk_app()
        elif args.method == "manual":
            patched_boot = patcher.patch_with_magiskboot(args.magiskboot)

        if patched_boot:
            # Generate flashing instructions
            patcher.generate_flash_instructions(patched_boot)

            print("\n" + "=" * 70)
            print("NEXT STEPS")
            print("=" * 70)
            print(f"\n1. Review instructions: {args.output / 'FLASH_INSTRUCTIONS.txt'}")
            print(f"2. Flash patched boot:  {patched_boot.absolute()}")
            print("3. Reboot and verify Magisk is working")
            print("\n⚠️  MAKE SURE TO BACKUP YOUR DATA FIRST!")

            return 0
        else:
            print("\nPatching failed", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
