#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    MagiskInstallerError,
    adb,
    detect_adb_device,
    detect_fastboot_device,
    fail,
    fastboot,
    get_active_slot,
    output_payload,
    verify_large_image,
    wait_for_adb_device,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flash a Magisk-patched boot image through fastboot.")
    parser.add_argument("--device", help="ADB serial for the target device before rebooting to fastboot.")
    parser.add_argument("--fastboot-serial", help="Explicit fastboot serial if it differs from the adb serial.")
    parser.add_argument("--boot-path", required=True, help="Local path to the patched boot image.")
    parser.add_argument("--partition", help="Partition to flash, such as boot, boot_a, or boot_b.")
    parser.add_argument("--reboot", action="store_true", help="Reboot the device after flashing.")
    parser.add_argument("--verify", action="store_true", help="Perform basic image sanity checks before flashing.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        boot_path = Path(args.boot_path).expanduser().resolve()
        if args.verify:
            verify_large_image(boot_path)
        elif not boot_path.is_file():
            raise MagiskInstallerError(f"Patched boot image was not found: {boot_path}")

        device = None
        active_slot = None
        if args.device:
            device = detect_adb_device(args.device)
            active_slot = get_active_slot(device)
            adb(device, "reboot", "bootloader")

        fastboot_serial = detect_fastboot_device(args.fastboot_serial)
        partition = args.partition
        if not partition:
            partition = f"boot_{active_slot}" if active_slot in {"a", "b"} else "boot"

        flash_result = fastboot(fastboot_serial, "flash", partition, str(boot_path))
        rebooted = False
        if args.reboot:
            fastboot(fastboot_serial, "reboot")
            rebooted = True
            if device:
                wait_for_adb_device(device, timeout=90)

        payload = {
            "ok": True,
            "adb_device": device,
            "fastboot_serial": fastboot_serial,
            "partition": partition,
            "boot_path": str(boot_path),
            "rebooted": rebooted,
            "stdout": flash_result.stdout.strip(),
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
