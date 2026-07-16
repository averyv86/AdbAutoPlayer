#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Sequence

MAGISK_PACKAGE = "com.topjohnwu.magisk"
GITHUB_API_BASE = "https://api.github.com/repos/topjohnwu/magisk"
JSON_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "adb-magisk-installer/1.0",
}


class MagiskInstallerError(RuntimeError):
    """Raised when an install phase cannot be completed safely."""


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def output_payload(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    for key, value in payload.items():
        if isinstance(value, (list, tuple)):
            printable = ", ".join(str(item) for item in value)
        else:
            printable = value
        print(f"{key}: {printable}")


def fail(message: str, as_json: bool = False, **extra: object) -> None:
    payload = {"ok": False, "error": message, **extra}
    output_payload(payload, as_json)
    raise SystemExit(1)


def ensure_binary(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise MagiskInstallerError(
            f"Required binary '{binary}' was not found in PATH. Install Android platform-tools first."
        )
    return resolved


def run_command(
    args: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(args),
            check=False,
            capture_output=capture_output,
            text=True,
            cwd=str(cwd) if cwd else None,
        )
    except OSError as exc:
        raise MagiskInstallerError(f"Failed to execute {' '.join(args)}: {exc}") from exc

    if check and completed.returncode != 0:
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        joined = "\n".join(part for part in (stdout, stderr) if part)
        raise MagiskInstallerError(
            f"Command failed ({' '.join(args)}): {joined or f'exit code {completed.returncode}'}"
        )
    return completed


def adb_base(device: str | None) -> list[str]:
    ensure_binary("adb")
    base = ["adb"]
    if device:
        base.extend(["-s", device])
    return base


def fastboot_base(serial: str | None) -> list[str]:
    ensure_binary("fastboot")
    base = ["fastboot"]
    if serial:
        base.extend(["-s", serial])
    return base


def adb(device: str | None, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_command([*adb_base(device), *args], check=check)


def fastboot(serial: str | None, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_command([*fastboot_base(serial), *args], check=check)


def adb_shell(device: str | None, command: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return adb(device, "shell", command, check=check)


def list_adb_devices() -> list[str]:
    completed = adb(None, "devices", check=True)
    devices: list[str] = []
    for line in completed.stdout.splitlines()[1:]:
        line = line.strip()
        if not line or "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state == "device":
            devices.append(serial)
    return devices


def detect_adb_device(preferred: str | None) -> str:
    if preferred:
        devices = list_adb_devices()
        if preferred not in devices:
            raise MagiskInstallerError(
                f"Requested adb device '{preferred}' is not connected. Connected devices: {devices or 'none'}"
            )
        return preferred

    devices = list_adb_devices()
    if not devices:
        raise MagiskInstallerError("No adb devices are connected.")
    if len(devices) > 1:
        raise MagiskInstallerError(
            f"Multiple adb devices detected ({', '.join(devices)}). Re-run with --device SERIAL."
        )
    return devices[0]


def wait_for_adb_device(device: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if device in list_adb_devices():
            return
        time.sleep(2)
    raise MagiskInstallerError(f"Timed out waiting for adb device '{device}' to come online.")


def list_fastboot_devices() -> list[str]:
    completed = fastboot(None, "devices", check=True)
    devices: list[str] = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if parts:
            devices.append(parts[0])
    return devices


def detect_fastboot_device(preferred: str | None = None, timeout: int = 30) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        devices = list_fastboot_devices()
        if preferred:
            if preferred in devices:
                return preferred
        elif len(devices) == 1:
            return devices[0]
        elif len(devices) > 1:
            raise MagiskInstallerError(
                f"Multiple fastboot devices detected ({', '.join(devices)}). Re-run with --fastboot-serial SERIAL."
            )
        time.sleep(2)

    if preferred:
        raise MagiskInstallerError(f"Timed out waiting for fastboot device '{preferred}'.")
    raise MagiskInstallerError("No fastboot device became available.")


def adb_package_installed(device: str, package_name: str = MAGISK_PACKAGE) -> bool:
    result = adb_shell(device, f"pm path {shlex.quote(package_name)}", check=False)
    return result.returncode == 0 and package_name in result.stdout


def adb_launch_package(device: str, package_name: str = MAGISK_PACKAGE) -> None:
    adb(device, "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1")


def adb_push(device: str, local_path: Path, remote_path: str) -> None:
    adb(device, "push", str(local_path), remote_path)


def adb_pull(device: str, remote_path: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    adb(device, "pull", remote_path, str(local_path))


def remote_path_exists(device: str, remote_path: str) -> bool:
    result = adb_shell(device, f"test -e {shlex.quote(remote_path)}", check=False)
    return result.returncode == 0


def remote_glob(device: str, pattern: str) -> list[str]:
    completed = adb_shell(device, f"ls -1 {pattern}", check=False)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def remote_basename(remote_path: str) -> str:
    return remote_path.replace("\\", "/").rstrip("/").split("/")[-1]


def local_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def github_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=JSON_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise MagiskInstallerError(f"GitHub API request failed ({exc.code}): {body}") from exc
    except urllib.error.URLError as exc:
        raise MagiskInstallerError(f"GitHub API request failed: {exc}") from exc


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers=JSON_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except urllib.error.URLError as exc:
        raise MagiskInstallerError(f"Failed to download {url}: {exc}") from exc
    return destination


def resolve_magisk_release(version: str) -> dict:
    version = version.strip().lower()
    if version == "latest":
        return github_json(f"{GITHUB_API_BASE}/releases/latest")

    normalized = version if version.startswith("v") else f"v{version}"
    return github_json(f"{GITHUB_API_BASE}/releases/tags/{normalized}")


def select_magisk_apk_asset(release: dict) -> dict:
    assets = release.get("assets", [])
    for asset in assets:
        name = str(asset.get("name", ""))
        if name.startswith("Magisk-v") and name.endswith(".apk"):
            return asset
    raise MagiskInstallerError("Could not locate a Magisk APK asset in the selected release.")


def get_prop(device: str, prop_name: str) -> str:
    completed = adb_shell(device, f"getprop {shlex.quote(prop_name)}", check=False)
    return completed.stdout.strip()


def get_active_slot(device: str) -> str | None:
    suffix = get_prop(device, "ro.boot.slot_suffix")
    if suffix in {"_a", "_b"}:
        return suffix[1:]

    completed = adb_shell(device, "bootctl get-current-slot", check=False)
    if completed.returncode == 0:
        slot = completed.stdout.strip()
        if slot == "0":
            return "a"
        if slot == "1":
            return "b"
    return None


def detect_boot_partitions(device: str, explicit_partition: str | None) -> list[str]:
    if explicit_partition:
        return [explicit_partition]

    completed = adb_shell(device, "ls -1 /dev/block/by-name", check=False)
    entries = set(completed.stdout.split()) if completed.returncode == 0 else set()
    slot = get_active_slot(device)

    candidates: list[str] = []
    if slot and f"boot_{slot}" in entries:
        candidates.append(f"boot_{slot}")
    for fallback in ("boot", "boot_a", "boot_b", "init_boot", "vendor_boot"):
        if fallback in entries and fallback not in candidates:
            candidates.append(fallback)
    if not candidates and explicit_partition is None:
        candidates.append("boot")
    return candidates


def adb_has_root(device: str) -> bool:
    result = adb_shell(device, "id -u", check=False)
    return result.returncode == 0 and result.stdout.strip() == "0"


def adb_has_su(device: str) -> bool:
    result = adb_shell(device, "command -v su", check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def adb_shell_root(device: str, command: str) -> subprocess.CompletedProcess[str]:
    if adb_has_root(device):
        return adb_shell(device, command, check=True)
    if adb_has_su(device):
        quoted = shlex.quote(command)
        return adb_shell(device, f"su -c {quoted}", check=True)
    raise MagiskInstallerError(
        "Root shell access is required for this operation. Boot into TWRP/recovery, enable adb root, or provide a stock boot image instead."
    )


def dump_uiautomator(device: str) -> str:
    remote_dump = "/sdcard/window_dump.xml"
    adb_shell(device, f"uiautomator dump {shlex.quote(remote_dump)}")
    completed = adb_shell(device, f"cat {shlex.quote(remote_dump)}", check=True)
    xml_text = completed.stdout.strip()
    if not xml_text.startswith("<?xml"):
        raise MagiskInstallerError("uiautomator dump did not return a valid XML hierarchy.")
    return xml_text


def parse_bounds(bounds: str) -> tuple[int, int]:
    left_top, right_bottom = bounds.split("][")
    left, top = left_top.lstrip("[").split(",")
    right, bottom = right_bottom.rstrip("]").split(",")
    x = (int(left) + int(right)) // 2
    y = (int(top) + int(bottom)) // 2
    return x, y


def find_nodes_by_text(xml_text: str, targets: Iterable[str], *, partial: bool = False) -> list[ET.Element]:
    root = ET.fromstring(xml_text)
    normalized_targets = [target.casefold() for target in targets]
    matches: list[ET.Element] = []
    for node in root.iter("node"):
        candidates = [node.attrib.get("text", ""), node.attrib.get("content-desc", "")]
        for candidate in candidates:
            folded = candidate.casefold()
            if any(
                target in folded if partial else folded == target
                for target in normalized_targets
            ):
                matches.append(node)
                break
    return matches


def tap(device: str, x: int, y: int) -> None:
    adb(device, "shell", "input", "tap", str(x), str(y))


def tap_first_text(
    device: str,
    texts: Iterable[str],
    *,
    partial: bool = False,
    index: int = 0,
) -> bool:
    xml_text = dump_uiautomator(device)
    nodes = find_nodes_by_text(xml_text, texts, partial=partial)
    if len(nodes) <= index:
        return False
    bounds = nodes[index].attrib.get("bounds")
    if not bounds:
        return False
    x, y = parse_bounds(bounds)
    tap(device, x, y)
    return True


def wait_for_text(device: str, texts: Iterable[str], timeout: int = 30, partial: bool = False) -> str | None:
    deadline = time.time() + timeout
    target_list = list(texts)
    while time.time() < deadline:
        try:
            xml_text = dump_uiautomator(device)
        except MagiskInstallerError:
            time.sleep(2)
            continue
        nodes = find_nodes_by_text(xml_text, target_list, partial=partial)
        if nodes:
            return nodes[0].attrib.get("text") or nodes[0].attrib.get("content-desc")
        time.sleep(2)
    return None


def wait_for_remote_glob(device: str, pattern: str, *, timeout: int = 120, baseline: Iterable[str] | None = None) -> list[str]:
    baseline_set = set(baseline or [])
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = remote_glob(device, pattern)
        new_files = [entry for entry in current if entry not in baseline_set]
        if new_files:
            return new_files
        time.sleep(3)
    return []


def verify_large_image(path: Path, *, minimum_bytes: int = 4 * 1024 * 1024) -> None:
    if not path.is_file():
        raise MagiskInstallerError(f"Expected image file does not exist: {path}")
    size = path.stat().st_size
    if size < minimum_bytes:
        raise MagiskInstallerError(
            f"Image file looks too small ({size} bytes): {path}. Refusing to continue."
        )


def verify_magisk_root(device: str) -> bool:
    result = adb_shell(device, "su -c id", check=False)
    return result.returncode == 0 and "uid=0" in result.stdout
