#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "requests>=2.31.0",
# ]
# ///

"""
ADB Magisk Download - Get latest Magisk APK and files from GitHub releases

Downloads Magisk APK and optionally boot image from GitHub releases.
Automatically detects latest version or downloads specific version.
Stores files locally for installation workflow.

Usage:
    uv run adb-magisk-download.py
    uv run adb-magisk-download.py --version 30.6
    uv run adb-magisk-download.py --version 30.6 --include-boot
    uv run adb-magisk-download.py --output-dir /tmp/magisk --json

Examples:
    # Download latest version
    uv run adb-magisk-download.py --output-dir /tmp/magisk

    # Download specific version
    uv run adb-magisk-download.py --version 30.6 --output-dir /tmp/magisk

    # Include boot image for patching
    uv run adb-magisk-download.py --version 30.6 --include-boot \\
        --output-dir /tmp/magisk

    # Get JSON output for integration
    uv run adb-magisk-download.py --version latest --json

Exit Codes:
    0 - Success (files downloaded)
    1 - Warning (partial download)
    2 - Error (download failed)
    3 - Critical (network/API error)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List
import click
import requests

# ========== SECTION 3: CONSTANTS ==========
MAGISK_REPO = "topjohnwu/Magisk"
GITHUB_API_URL = f"https://api.github.com/repos/{MAGISK_REPO}/releases"
GITHUB_RELEASES_URL = f"https://github.com/{MAGISK_REPO}/releases/download"
MAGISK_PACKAGE = "com.topjohnwu.magisk"
TIMEOUT = 30

# ========== SECTION 4: DATA MODELS ==========
@dataclass
class DownloadedFile:
    """Information about downloaded file."""
    filename: str
    size_bytes: int
    local_path: str
    url: str
    downloaded: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class MagiskDownloadResult:
    """Result of Magisk download operation."""
    success: bool
    version: str = ""
    timestamp: float = 0.0
    duration: float = 0.0
    files: List[DownloadedFile] = field(default_factory=list)
    output_dir: str = ""
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        data = asdict(self)
        data['files'] = [f.to_dict() for f in self.files]
        return data

# ========== SECTION 5: HELPER FUNCTIONS ==========
def get_latest_release() -> Optional[dict]:
    """Get latest Magisk release info from GitHub API."""
    try:
        response = requests.get(
            GITHUB_API_URL,
            timeout=TIMEOUT,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        response.raise_for_status()
        releases = response.json()
        if releases:
            return releases[0]  # Latest release
        return None
    except Exception as e:
        return None

def get_release_by_version(version: str) -> Optional[dict]:
    """Get specific Magisk release by version."""
    try:
        url = f"{GITHUB_API_URL}/tags/v{version}"
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

def extract_version_from_release(release: dict) -> str:
    """Extract version number from release tag."""
    tag = release.get("tag_name", "unknown")
    return tag.lstrip('v')

def find_apk_in_release(release: dict) -> Optional[str]:
    """Find APK filename in release assets."""
    assets = release.get("assets", [])
    for asset in assets:
        filename = asset.get("name", "")
        if filename.endswith(".apk") and "Magisk" in filename:
            return asset.get("browser_download_url")
    return None

def find_boot_in_release(release: dict) -> Optional[str]:
    """Find boot image in release assets."""
    assets = release.get("assets", [])
    for asset in assets:
        filename = asset.get("name", "")
        if "boot" in filename and filename.endswith(".img"):
            return asset.get("browser_download_url")
    return None

def download_file(url: str, output_path: Path, filename: str) -> tuple[bool, Optional[str]]:
    """Download file from URL to local path."""
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if output_path.exists() and output_path.stat().st_size > 0:
            return True, None
        else:
            return False, f"Downloaded file is empty: {output_path}"

    except Exception as e:
        return False, str(e)

# ========== SECTION 6: CORE LOGIC ==========
def download_magisk(version: str = "latest", include_boot: bool = False,
                   output_dir: str = "/tmp/magisk") -> MagiskDownloadResult:
    """Download Magisk files."""
    start_time = time.time()
    result = MagiskDownloadResult(
        success=False,
        version=version,
        timestamp=start_time,
        output_dir=output_dir
    )

    # Step 1: Get release info
    if version.lower() == "latest":
        release = get_latest_release()
    else:
        release = get_release_by_version(version)

    if not release:
        result.error = f"Release not found: {version}"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    version = extract_version_from_release(release)
    result.version = version

    # Step 2: Find APK
    apk_url = find_apk_in_release(release)
    if not apk_url:
        result.error = "No APK found in release"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 3: Download APK
    apk_filename = f"Magisk-v{version}.apk"
    apk_path = Path(output_dir) / apk_filename

    apk_downloaded, apk_error = download_file(apk_url, apk_path, apk_filename)
    result.files.append(DownloadedFile(
        filename=apk_filename,
        size_bytes=apk_path.stat().st_size if apk_path.exists() else 0,
        local_path=str(apk_path),
        url=apk_url,
        downloaded=apk_downloaded,
        error=apk_error
    ))

    if not apk_downloaded:
        result.error = f"Failed to download APK: {apk_error}"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 4: Download boot image if requested
    if include_boot:
        boot_url = find_boot_in_release(release)
        if boot_url:
            boot_filename = f"boot-v{version}.img"
            boot_path = Path(output_dir) / boot_filename

            boot_downloaded, boot_error = download_file(boot_url, boot_path, boot_filename)
            result.files.append(DownloadedFile(
                filename=boot_filename,
                size_bytes=boot_path.stat().st_size if boot_path.exists() else 0,
                local_path=str(boot_path),
                url=boot_url,
                downloaded=boot_downloaded,
                error=boot_error
            ))

    # All files successfully downloaded
    result.success = all(f.downloaded for f in result.files)
    result.exit_code = 0 if result.success else 1
    result.duration = time.time() - start_time

    return result

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: MagiskDownloadResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Downloaded Magisk v{result.version}")
    else:
        lines.append(f"❌ Failed to download Magisk v{result.version}")

    lines.append(f"  Output Directory: {result.output_dir}")
    lines.append(f"  Files Downloaded: {len(result.files)}")

    for file in result.files:
        status = "✅" if file.downloaded else "❌"
        size_mb = file.size_bytes / (1024*1024)
        lines.append(f"  {status} {file.filename} ({size_mb:.1f} MB)")
        if file.error:
            lines.append(f"     Error: {file.error}")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: MagiskDownloadResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--version',
    type=str,
    default='latest',
    help='Magisk version to download (default: latest)'
)
@click.option(
    '--include-boot',
    is_flag=True,
    help='Include boot image in download'
)
@click.option(
    '--output-dir',
    type=str,
    default='/tmp/magisk',
    help='Output directory for downloaded files'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(version: str, include_boot: bool, output_dir: str,
        output_json: bool) -> None:
    """
    Download Magisk APK and files from GitHub.

    Downloads latest or specific version of Magisk from topjohnwu/Magisk
    releases. Optionally includes boot image for installation workflow.

    Examples:
        uv run adb-magisk-download.py
        uv run adb-magisk-download.py --version 30.6
        uv run adb-magisk-download.py --version 30.6 --include-boot
    """
    # Download files
    result = download_magisk(
        version=version,
        include_boot=include_boot,
        output_dir=output_dir
    )

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
