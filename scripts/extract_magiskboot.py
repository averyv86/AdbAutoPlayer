#!/usr/bin/env python3
"""Extract magiskboot binary from Magisk APK.

This script extracts the magiskboot binary from a Magisk APK file
for use in boot image patching operations.

Usage:
    python extract_magiskboot.py [--apk PATH] [--output DIR] [--arch ARCH]

Requirements:
    - Python 3.11+
    - ADB (if pulling from device)
    - Internet connection (if downloading from GitHub)
"""

import argparse
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

# Magisk GitHub releases URL
MAGISK_RELEASES_URL = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"
MAGISK_APK_DEVICE_PATH = "/data/app/~~GgyKMNhPlOVcDnaGy-6vAg==/com.topjohnwu.magisk-6wY7n0LDQnjotyIN5daQhw==/base.apk"


class MagiskBootExtractor:
    """Extract magiskboot from Magisk APK."""

    def __init__(self, output_dir: Path, architecture: str = "arm64-v8a"):
        """Initialize extractor.

        Args:
            output_dir: Directory to extract magiskboot to
            architecture: Target architecture (arm64-v8a, armeabi-v7a, x86, x86_64)
        """
        self.output_dir = output_dir
        self.architecture = architecture
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_latest_magisk(self) -> Path:
        """Download latest Magisk APK from GitHub releases.

        Returns:
            Path to downloaded APK file
        """
        import json
        import urllib.request

        print("Fetching latest Magisk release information...")

        try:
            with urllib.request.urlopen(MAGISK_RELEASES_URL) as response:
                release_data = json.loads(response.read())

            version = release_data["tag_name"]
            apk_url = None

            # Find APK asset in release
            for asset in release_data["assets"]:
                if asset["name"].endswith(".apk"):
                    apk_url = asset["browser_download_url"]
                    break

            if not apk_url:
                raise RuntimeError("No APK found in latest release")

            print(f"Downloading Magisk {version}...")
            apk_path = self.output_dir / f"Magisk-{version}.apk"

            urllib.request.urlretrieve(apk_url, apk_path)
            print(f"Downloaded to: {apk_path}")

            return apk_path

        except Exception as e:
            raise RuntimeError(f"Failed to download Magisk: {e}") from e

    def pull_from_device(self, device_path: Optional[str] = None) -> Path:
        """Pull Magisk APK from Android device via ADB.

        Args:
            device_path: Path to APK on device (auto-detected if None)

        Returns:
            Path to pulled APK file
        """
        if device_path is None:
            # Try to find Magisk package path
            print("Searching for Magisk APK on device...")
            try:
                result = subprocess.run(
                    ["adb", "shell", "pm", "path", "com.topjohnwu.magisk"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Output: "package:/data/app/.../base.apk"
                device_path = result.stdout.strip().replace("package:", "")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Magisk not found on device. Is it installed? Error: {e}"
                ) from e

        print(f"Pulling APK from device: {device_path}")
        apk_path = self.output_dir / "Magisk.apk"

        try:
            subprocess.run(
                ["adb", "pull", device_path, str(apk_path)],
                check=True,
                capture_output=True,
            )
            print(f"Pulled to: {apk_path}")
            return apk_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to pull APK from device: {e}") from e

    def extract_magiskboot(self, apk_path: Path) -> Path:
        """Extract magiskboot binary from APK.

        Args:
            apk_path: Path to Magisk APK file

        Returns:
            Path to extracted magiskboot binary
        """
        print(f"Extracting magiskboot from {apk_path}...")

        # Possible paths in APK
        possible_paths = [
            f"lib/{self.architecture}/libmagiskboot.so",
            f"lib/{self.architecture}/libmagisk64.so",
            f"lib/{self.architecture}/libmagisk32.so",
        ]

        try:
            with zipfile.ZipFile(apk_path, "r") as apk_zip:
                # List all files to debug
                all_files = apk_zip.namelist()
                lib_files = [f for f in all_files if f.startswith("lib/")]

                print(f"Available architectures: {set(f.split('/')[1] for f in lib_files if len(f.split('/')) > 1)}")

                # Try to find magiskboot
                magiskboot_path = None
                for path in possible_paths:
                    if path in all_files:
                        magiskboot_path = path
                        print(f"Found: {path}")
                        break

                if not magiskboot_path:
                    # Show available files for debugging
                    print(f"\nAvailable lib files for {self.architecture}:")
                    arch_files = [f for f in lib_files if self.architecture in f]
                    for f in arch_files:
                        print(f"  - {f}")

                    raise RuntimeError(
                        f"magiskboot not found for architecture {self.architecture}"
                    )

                # Extract binary
                output_path = self.output_dir / "magiskboot"
                with apk_zip.open(magiskboot_path) as source:
                    with open(output_path, "wb") as target:
                        target.write(source.read())

                # Make executable (Unix-like systems)
                if os.name != "nt":  # Not Windows
                    current_permissions = output_path.stat().st_mode
                    output_path.chmod(
                        current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                    )

                print(f"Extracted to: {output_path}")
                print(f"Made executable: {oct(output_path.stat().st_mode)}")

                return output_path

        except zipfile.BadZipFile as e:
            raise RuntimeError(f"Invalid APK file: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to extract magiskboot: {e}") from e

    def verify_binary(self, binary_path: Path) -> bool:
        """Verify extracted binary is valid.

        Args:
            binary_path: Path to magiskboot binary

        Returns:
            True if binary is valid
        """
        print(f"\nVerifying binary: {binary_path}")

        # Check file exists and is executable
        if not binary_path.exists():
            print("ERROR: Binary does not exist")
            return False

        if not os.access(binary_path, os.X_OK) and os.name != "nt":
            print("WARNING: Binary is not executable (Unix-like system)")
            return False

        # Check file size (magiskboot is typically 200-500 KB)
        size_kb = binary_path.stat().st_size / 1024
        print(f"Binary size: {size_kb:.1f} KB")

        if size_kb < 100:
            print("WARNING: Binary seems too small")
            return False

        if size_kb > 2048:
            print("WARNING: Binary seems too large")
            return False

        print("Binary verification: OK")
        return True


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract magiskboot binary from Magisk APK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download latest Magisk and extract
  python extract_magiskboot.py

  # Pull from connected Android device
  python extract_magiskboot.py --from-device

  # Extract from local APK file
  python extract_magiskboot.py --apk Magisk-v27.0.apk

  # Specify architecture and output directory
  python extract_magiskboot.py --arch armeabi-v7a --output ./tools/
        """,
    )

    parser.add_argument(
        "--apk",
        type=Path,
        help="Path to Magisk APK file (downloads latest if not specified)",
    )

    parser.add_argument(
        "--from-device",
        action="store_true",
        help="Pull APK from connected Android device via ADB",
    )

    parser.add_argument(
        "--device-path",
        type=str,
        default=MAGISK_APK_DEVICE_PATH,
        help="Custom APK path on device (default: auto-detect via pm)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./magisk_tools"),
        help="Output directory (default: ./magisk_tools)",
    )

    parser.add_argument(
        "--arch",
        choices=["arm64-v8a", "armeabi-v7a", "x86", "x86_64"],
        default="arm64-v8a",
        help="Target architecture (default: arm64-v8a for Snapdragon 8 Gen 1)",
    )

    args = parser.parse_args()

    # Initialize extractor
    extractor = MagiskBootExtractor(args.output, args.arch)

    try:
        # Determine APK source
        if args.from_device:
            apk_path = extractor.pull_from_device(
                args.device_path if args.device_path != MAGISK_APK_DEVICE_PATH else None
            )
        elif args.apk:
            if not args.apk.exists():
                print(f"ERROR: APK file not found: {args.apk}", file=sys.stderr)
                sys.exit(1)
            apk_path = args.apk
        else:
            # Download latest from GitHub
            apk_path = extractor.download_latest_magisk()

        # Extract magiskboot
        magiskboot_path = extractor.extract_magiskboot(apk_path)

        # Verify binary
        if extractor.verify_binary(magiskboot_path):
            print("\n" + "=" * 60)
            print("SUCCESS! magiskboot extracted successfully")
            print("=" * 60)
            print(f"\nBinary location: {magiskboot_path.absolute()}")
            print(f"Architecture: {args.arch}")
            print(f"\nUsage:")
            print(f"  {magiskboot_path} unpack boot.img")
            print(f"  {magiskboot_path} repack boot.img")
            print(f"  {magiskboot_path} --help")
            return 0
        else:
            print("\nWARNING: Binary verification failed", file=sys.stderr)
            print("The binary may not work correctly", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
