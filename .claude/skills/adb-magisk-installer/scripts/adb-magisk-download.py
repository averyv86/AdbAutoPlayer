#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    MagiskInstallerError,
    download_file,
    fail,
    local_sha256,
    output_payload,
    resolve_magisk_release,
    select_magisk_apk_asset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Magisk APK assets from GitHub releases.")
    parser.add_argument("--version", default="latest", help="Magisk release version, such as 30.6 or latest.")
    parser.add_argument("--output-dir", required=True, help="Directory where downloaded files will be stored.")
    parser.add_argument(
        "--include-boot",
        action="store_true",
        help="Also download a stock boot image when --boot-url is provided.",
    )
    parser.add_argument(
        "--boot-url",
        help="Optional direct URL to a device-specific boot image. Useful with --include-boot.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        release = resolve_magisk_release(args.version)
        asset = select_magisk_apk_asset(release)
        apk_name = asset["name"]
        apk_url = asset["browser_download_url"]
        apk_path = output_dir / apk_name
        download_file(apk_url, apk_path)

        boot_path = None
        warning = None
        if args.include_boot:
            if args.boot_url:
                boot_name = Path(args.boot_url.split("?", 1)[0]).name or "boot.img"
                boot_path = output_dir / boot_name
                download_file(args.boot_url, boot_path)
            else:
                warning = (
                    "--include-boot was requested without --boot-url. "
                    "Magisk APK was downloaded, but the boot image must be extracted from the device or supplied later."
                )

        payload = {
            "ok": True,
            "requested_version": args.version,
            "resolved_tag": release.get("tag_name"),
            "release_name": release.get("name"),
            "apk_name": apk_name,
            "apk_path": str(apk_path),
            "apk_sha256": local_sha256(apk_path),
            "boot_path": str(boot_path) if boot_path else None,
            "warning": warning,
            "next_step": "Install the APK with adb-magisk-install-app.py.",
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
