#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import time
from pathlib import Path

from common import (
    MAGISK_PACKAGE,
    MagiskInstallerError,
    adb_launch_package,
    adb_package_installed,
    adb_pull,
    adb_push,
    adb_shell,
    detect_adb_device,
    dump_uiautomator,
    fail,
    output_payload,
    remote_basename,
    remote_glob,
    remote_path_exists,
    tap_first_text,
    wait_for_remote_glob,
    wait_for_text,
)


INSTALL_LABELS = ["Install"]
PATCH_LABELS = ["Select and Patch a File", "Patch a File"]
CONFIRM_LABELS = ["LET'S GO", "Let's Go", "START", "Start", "OK"]
DOWNLOAD_LABELS = ["Downloads", "Download"]


def ensure_boot_in_downloads(device: str, boot_path: str) -> str:
    if not remote_path_exists(device, boot_path):
        raise MagiskInstallerError(f"Boot image was not found on the device: {boot_path}")

    basename = remote_basename(boot_path)
    target = f"/sdcard/Download/{basename}"
    if boot_path != target:
        adb_shell(device, f"cp {shlex.quote(boot_path)} {shlex.quote(target)}")
    adb_shell(
        device,
        f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{target}",
        check=False,
    )
    return target


def tap_install_button(device: str) -> None:
    if tap_first_text(device, INSTALL_LABELS, index=0):
        time.sleep(2)
        if wait_for_text(device, PATCH_LABELS, timeout=8, partial=True):
            return
    if tap_first_text(device, INSTALL_LABELS, index=1):
        time.sleep(2)
        if wait_for_text(device, PATCH_LABELS, timeout=8, partial=True):
            return
    raise MagiskInstallerError(
        "Could not reach the Magisk install flow automatically. Unlock the device, open Magisk once, and try again."
    )


def select_boot_file(device: str, basename: str) -> None:
    if not wait_for_text(device, PATCH_LABELS, timeout=20, partial=True):
        raise MagiskInstallerError("Magisk patch options did not appear in time.")
    if not tap_first_text(device, PATCH_LABELS, partial=True):
        raise MagiskInstallerError("Could not tap the 'Select and Patch a File' option.")

    if not wait_for_text(device, [basename, *DOWNLOAD_LABELS], timeout=20, partial=True):
        raise MagiskInstallerError(
            "Android's file picker did not show the boot image. Move the file to /sdcard/Download and keep the screen unlocked."
        )

    if not tap_first_text(device, [basename], partial=True):
        tap_first_text(device, DOWNLOAD_LABELS, partial=True)
        time.sleep(2)
        if not tap_first_text(device, [basename], partial=True):
            xml_snapshot = dump_uiautomator(device)
            raise MagiskInstallerError(
                "Could not select the boot image inside the Android file picker. "
                f"UI snapshot length: {len(xml_snapshot)} characters."
            )


def confirm_patch(device: str) -> None:
    if wait_for_text(device, CONFIRM_LABELS, timeout=20, partial=True):
        if tap_first_text(device, CONFIRM_LABELS, partial=True):
            return
    raise MagiskInstallerError("Could not find the final confirmation button to start patching.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch a boot image on-device using the Magisk app UI.")
    parser.add_argument("--device", help="ADB serial for the target device.")
    parser.add_argument("--boot-path", required=True, help="Boot image path on the Android device.")
    parser.add_argument("--output-path", help="Optional local path to pull the patched image to automatically.")
    parser.add_argument("--wait-completion", action="store_true", help="Wait for Magisk to finish patching.")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum number of seconds to wait for a patched image.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args()

    try:
        device = detect_adb_device(args.device)
        if not adb_package_installed(device, MAGISK_PACKAGE):
            raise MagiskInstallerError("The Magisk app is not installed on the target device.")

        staged_boot = ensure_boot_in_downloads(device, args.boot_path)
        existing = remote_glob(device, "/sdcard/Download/magisk_patched*.img")
        adb_launch_package(device, MAGISK_PACKAGE)
        if not wait_for_text(device, ["Install", "Installed", "Magisk"], timeout=25, partial=True):
            raise MagiskInstallerError("Magisk did not finish launching on the device.")

        tap_install_button(device)
        select_boot_file(device, remote_basename(staged_boot))
        confirm_patch(device)

        patched_remote = None
        patched_local = None
        if args.wait_completion or args.output_path:
            matches = wait_for_remote_glob(
                device,
                "/sdcard/Download/magisk_patched*.img",
                timeout=args.timeout,
                baseline=existing,
            )
            if not matches:
                raise MagiskInstallerError(
                    "Magisk did not produce a patched image in time. Keep the device awake and confirm there is enough free storage."
                )
            patched_remote = sorted(matches)[-1]
            if args.output_path:
                patched_local = Path(args.output_path).expanduser().resolve()
                adb_pull(device, patched_remote, patched_local)

        payload = {
            "ok": True,
            "device": device,
            "boot_path": staged_boot,
            "patched_remote": patched_remote,
            "patched_local": str(patched_local) if patched_local else None,
        }
        output_payload(payload, args.json)
    except MagiskInstallerError as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
