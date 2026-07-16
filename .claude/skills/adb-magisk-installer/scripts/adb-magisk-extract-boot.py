#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    MagiskInstallerError,
    adb_pull,
    adb_shell,
    adb_shell_root,
    detect_adb_device,
    detect_boot_partitions,
    fail,
    get_active_slot,
    output_payload,
    verify_large_image,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract a boot image from a connected device using adb.")
    parser.add_argument("--device", help="ADB serial for the target device.")
    parser.add_argument("--partition", help="Explicit partition name, such as boot_a, boot_b, boot, or vendor_boot.")
    parser.add_argument("--output-path", required=True, help="Local path where the extracted image will be saved.")
    parser.add_argument("--verify", action="store_true", help="Validate that the extracted image looks sane.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        device = detect_adb_device(args.device)
        output_path = Path(args.output_path).expanduser().resolve()
        candidates = detect_boot_partitions(device, args.partition)
        if not candidates:
            raise MagiskInstallerError("Could not determine any candidate boot partitions.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        remote_temp = "/data/local/tmp/boot-from-device.img"
        chosen_partition = None
        root_method = "adbd-root" if adb_shell(device, "id -u", check=False).stdout.strip() == "0" else "su"

        for partition in candidates:
            adb_shell(device, f"rm -f {remote_temp}", check=False)
            try:
                adb_shell_root(
                    device,
                    f"dd if=/dev/block/by-name/{partition} of={remote_temp} bs=4M status=none",
                )
                chosen_partition = partition
                break
            except MagiskInstallerError:
                continue

        if not chosen_partition:
            raise MagiskInstallerError(
                "Unable to read any boot-like partition from the device. "
                "If Magisk is not yet installed systemlessly, boot into TWRP or provide a stock boot image manually."
            )

        adb_pull(device, remote_temp, output_path)
        adb_shell(device, f"rm -f {remote_temp}", check=False)

        if args.verify:
            verify_large_image(output_path)

        payload = {
            "ok": True,
            "device": device,
            "partition": chosen_partition,
            "slot": get_active_slot(device),
            "root_method": root_method,
            "output_path": str(output_path),
            "size_bytes": output_path.stat().st_size,
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
