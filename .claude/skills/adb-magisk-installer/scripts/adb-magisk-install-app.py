#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    MAGISK_PACKAGE,
    MagiskInstallerError,
    adb,
    adb_launch_package,
    adb_package_installed,
    detect_adb_device,
    fail,
    output_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the Magisk app onto a connected Android device.")
    parser.add_argument("--device", help="ADB serial, such as 127.0.0.1:5555 or an attached USB device.")
    parser.add_argument("--apk-path", required=True, help="Path to the downloaded Magisk APK.")
    parser.add_argument("--force", action="store_true", help="Reinstall or replace the app if it already exists.")
    parser.add_argument("--verify", action="store_true", help="Verify installation and launch the app once.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        apk_path = Path(args.apk_path).expanduser().resolve()
        if not apk_path.is_file():
            raise MagiskInstallerError(f"APK file was not found: {apk_path}")

        device = detect_adb_device(args.device)
        install_args = ["install"]
        if args.force:
            install_args.append("-r")
        install_args.append(str(apk_path))
        result = adb(device, *install_args)

        verified = False
        if args.verify:
            verified = adb_package_installed(device, MAGISK_PACKAGE)
            if not verified:
                raise MagiskInstallerError("Package installation completed but the Magisk package is not visible to pm.")
            adb_launch_package(device, MAGISK_PACKAGE)

        payload = {
            "ok": True,
            "device": device,
            "apk_path": str(apk_path),
            "package": MAGISK_PACKAGE,
            "verified": verified,
            "stdout": result.stdout.strip(),
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
