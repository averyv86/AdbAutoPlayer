#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from common import (
    MAGISK_PACKAGE,
    MagiskInstallerError,
    adb_launch_package,
    adb_package_installed,
    detect_adb_device,
    fail,
    output_payload,
    wait_for_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Magisk app on-device and optionally wait for text to appear.")
    parser.add_argument("--device", help="ADB serial for the target device.")
    parser.add_argument("--wait-text", help="Optional text substring to wait for after launching.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds to wait for text to appear.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        device = detect_adb_device(args.device)
        if not adb_package_installed(device, MAGISK_PACKAGE):
            raise MagiskInstallerError("Magisk app is not installed on the target device.")

        adb_launch_package(device, MAGISK_PACKAGE)

        resolved_text = None
        if args.wait_text:
            resolved_text = wait_for_text(
                device,
                [args.wait_text],
                timeout=args.timeout,
                partial=True,
            )
            if not resolved_text:
                raise MagiskInstallerError(f"Timed out waiting for text '{args.wait_text}' to appear in Magisk app UI.")

        payload = {
            "ok": True,
            "device": device,
            "package": MAGISK_PACKAGE,
            "launched": True,
            "resolved_text": resolved_text,
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
