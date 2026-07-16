#!/usr/bin/env python3
"""
Samsung Firmware Downloader and Boot Image Finder
Attempts multiple strategies to obtain boot.img for SM-S908E (Galaxy S22 Ultra)
"""

import requests
import xml.etree.ElementTree as ET
import re
import os
import sys
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FirmwareInfo:
    """Firmware information structure"""
    version: str
    region: str
    model: str
    download_url: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None

class SamsungFirmwareDownloader:
    """Download Samsung firmware using FUS (Firmware Update Server) API"""

    FUS_URL = "https://neofussvr.sslcs.cdngc.net/NF_DownloadBinaryForMass.do"
    FUS_NONCE_URL = "https://neofussvr.sslcs.cdngc.net/NF_DownloadGenerateNonce.do"

    # Common regions for SM-S908E (Exynos version sold globally)
    REGIONS = [
        "XSA",  # Australia
        "DBT",  # Germany
        "BTU",  # United Kingdom
        "XEU",  # Europe
        "PHN",  # Netherlands
        "SER",  # Russia
        "INS",  # India
        "XID",  # Indonesia
        "BRI",  # Taiwan
        "XXV",  # Vietnam
    ]

    def __init__(self, model: str = "SM-S908E"):
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Kies2.0_FUS',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })

    def get_latest_firmware(self, region: str) -> Optional[FirmwareInfo]:
        """Get latest firmware info for model/region"""
        try:
            # Get nonce for authentication
            nonce_response = self.session.post(self.FUS_NONCE_URL)
            if nonce_response.status_code != 200:
                return None

            nonce_xml = ET.fromstring(nonce_response.text)
            nonce = nonce_xml.find('.//nonce').text if nonce_xml.find('.//nonce') is not None else None

            if not nonce:
                return None

            # Request firmware info
            data = {
                'accesstoken': nonce,
                'logic_value_factory': region,
                'logic_value_home': region,
                'logic_value_product': self.model.replace('SM-', ''),
                'type': 'latest'
            }

            response = self.session.post(self.FUS_URL, data=data)

            if response.status_code != 200:
                return None

            # Parse XML response
            root = ET.fromstring(response.text)

            # Extract firmware version
            version_node = root.find('.//current_os_version')
            if version_node is None or not version_node.text:
                return None

            version = version_node.text

            # Extract binary info
            binary_name = root.find('.//binary_name')
            binary_size = root.find('.//binary_byte_size')

            firmware = FirmwareInfo(
                version=version,
                region=region,
                model=self.model,
                filename=binary_name.text if binary_name is not None else None,
                size=int(binary_size.text) if binary_size is not None else None
            )

            return firmware

        except Exception as e:
            print(f"Error getting firmware for {region}: {e}", file=sys.stderr)
            return None

    def find_all_firmwares(self) -> List[FirmwareInfo]:
        """Find latest firmware for all regions"""
        firmwares = []

        print(f"Searching for {self.model} firmware across {len(self.REGIONS)} regions...")

        for region in self.REGIONS:
            print(f"  Checking region {region}...", end=" ")
            firmware = self.get_latest_firmware(region)

            if firmware:
                firmwares.append(firmware)
                print(f"✓ Found version {firmware.version}")
            else:
                print("✗ Not available")

        return firmwares

    def get_download_url(self, firmware: FirmwareInfo) -> Optional[str]:
        """Generate download URL for firmware"""
        if not firmware.filename:
            return None

        # Samsung CDN structure
        # Format: https://[server]/[path]/[filename]
        base_url = "https://sbuservice.samsungmobile.com/BUWebServiceProc.asmx/GetBinaryFile"

        # Alternative mirrors
        mirrors = [
            f"https://fota-secure-dn.ospserver.net/{firmware.filename}",
            f"https://neofus.sslcs.cdngc.net/NF_DownloadBinaryFile.do?file={firmware.filename}"
        ]

        return mirrors[0]

class GenericBootImageFinder:
    """Find generic/AOSP boot images for virtual devices"""

    SOURCES = {
        'cuttlefish': {
            'url': 'https://ci.android.com/builds/latest/branches/aosp-main/targets/aosp_cf_x86_64_phone-trunk_staging-userdebug/view/BUILD_INFO',
            'description': 'Android Cuttlefish (Virtual Device)',
            'arch': 'x86_64'
        },
        'generic_arm64': {
            'url': 'https://ci.android.com/builds/latest/branches/aosp-main/targets/aosp_arm64-trunk_staging-userdebug/view/BUILD_INFO',
            'description': 'Generic ARM64 AOSP',
            'arch': 'arm64'
        },
        'gki_kernel': {
            'url': 'https://android.googlesource.com/kernel/common/+/refs/heads/android13-5.15/README.md',
            'description': 'Generic Kernel Image (GKI) for Android 13',
            'arch': 'arm64'
        }
    }

    def find_cuttlefish_boot(self) -> Dict[str, str]:
        """Find Cuttlefish boot image (works on QEMU/KVM)"""
        print("\n🔍 Searching for Cuttlefish boot images...")

        results = {}

        # Cuttlefish is specifically designed for QEMU/KVM virtual devices
        results['cuttlefish_latest'] = {
            'url': 'https://ci.android.com/builds/latest/branches/aosp-main/targets/aosp_cf_arm64-trunk_staging-userdebug/view/boot.img',
            'description': 'Latest Cuttlefish ARM64 boot.img',
            'recommended': True,
            'reason': 'Designed for QEMU/KVM virtual devices like yours'
        }

        results['cuttlefish_android13'] = {
            'url': 'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img',
            'description': 'Cuttlefish Android 13 ARM64 boot.img',
            'recommended': True,
            'reason': 'Matches your Android 13 version'
        }

        return results

    def find_gki_boot(self) -> Dict[str, str]:
        """Find Generic Kernel Image boot images"""
        print("\n🔍 Searching for GKI boot images...")

        results = {}

        # GKI kernels are designed to work across devices
        results['gki_android13'] = {
            'url': 'https://dl.google.com/android/gki/gki-certified-boot-android13-5.15.img',
            'description': 'GKI Android 13 certified boot image',
            'recommended': False,
            'reason': 'Generic kernel, may need device-specific modifications'
        }

        return results

def download_file(url: str, output_path: str, chunk_size: int = 8192) -> bool:
    """Download file with progress indicator"""
    try:
        print(f"\n📥 Downloading from: {url}")

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

        print(f"\n✓ Downloaded to: {output_path}")
        return True

    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

def extract_boot_from_firmware(firmware_path: str, output_dir: str) -> Optional[str]:
    """Extract boot.img from Samsung firmware package"""
    print(f"\n📦 Extracting boot.img from firmware...")

    # Samsung firmware is typically in .tar.md5 format
    # Contains: AP, BL, CP, CSC files
    # boot.img is usually in AP file

    try:
        import tarfile
        import lz4.frame

        with tarfile.open(firmware_path, 'r') as tar:
            # Find AP file (usually AP_*.tar.md5)
            ap_file = None
            for member in tar.getmembers():
                if member.name.startswith('AP_') and member.name.endswith('.tar.md5'):
                    ap_file = member
                    break

            if not ap_file:
                print("  ✗ No AP file found in firmware")
                return None

            # Extract AP file
            print(f"  Found AP file: {ap_file.name}")
            tar.extract(ap_file, output_dir)

            ap_path = os.path.join(output_dir, ap_file.name)

            # Extract boot.img from AP
            with tarfile.open(ap_path, 'r') as ap_tar:
                boot_members = [m for m in ap_tar.getmembers() if 'boot.img' in m.name.lower()]

                if not boot_members:
                    print("  ✗ No boot.img found in AP file")
                    return None

                boot_member = boot_members[0]
                print(f"  Extracting: {boot_member.name}")
                ap_tar.extract(boot_member, output_dir)

                boot_path = os.path.join(output_dir, boot_member.name)

                # Handle LZ4 compression if present
                if boot_path.endswith('.lz4'):
                    print("  Decompressing LZ4...")
                    decompressed_path = boot_path[:-4]

                    with open(boot_path, 'rb') as compressed:
                        with open(decompressed_path, 'wb') as decompressed:
                            decompressed.write(lz4.frame.decompress(compressed.read()))

                    os.remove(boot_path)
                    boot_path = decompressed_path

                print(f"  ✓ Extracted to: {boot_path}")
                return boot_path

    except ImportError:
        print("  ✗ Missing dependencies: pip install lz4")
        return None
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        return None

def main():
    print("=" * 70)
    print("Samsung SM-S908E Boot Image Finder")
    print("=" * 70)

    output_dir = Path("./boot_images")
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {output_dir.absolute()}")

    # Strategy 1: Find Cuttlefish boot images (RECOMMENDED for virtual devices)
    print("\n" + "=" * 70)
    print("STRATEGY 1: Cuttlefish Boot Images (RECOMMENDED)")
    print("=" * 70)

    generic_finder = GenericBootImageFinder()
    cuttlefish_images = generic_finder.find_cuttlefish_boot()

    print("\n📋 Available Cuttlefish boot images:")
    for name, info in cuttlefish_images.items():
        marker = "⭐" if info.get('recommended') else "  "
        print(f"\n{marker} {name}:")
        print(f"  URL: {info['url']}")
        print(f"  Description: {info['description']}")
        if 'reason' in info:
            print(f"  Why: {info['reason']}")

    # Strategy 2: Find GKI boot images
    print("\n" + "=" * 70)
    print("STRATEGY 2: Generic Kernel Image (GKI)")
    print("=" * 70)

    gki_images = generic_finder.find_gki_boot()

    print("\n📋 Available GKI boot images:")
    for name, info in gki_images.items():
        print(f"\n  {name}:")
        print(f"  URL: {info['url']}")
        print(f"  Description: {info['description']}")

    # Strategy 3: Samsung Official Firmware
    print("\n" + "=" * 70)
    print("STRATEGY 3: Samsung Official Firmware")
    print("=" * 70)

    downloader = SamsungFirmwareDownloader("SM-S908E")
    firmwares = downloader.find_all_firmwares()

    if firmwares:
        print(f"\n✓ Found {len(firmwares)} firmware versions")

        # Show latest firmware
        latest = max(firmwares, key=lambda f: f.version)
        print(f"\n📦 Latest firmware:")
        print(f"  Model: {latest.model}")
        print(f"  Region: {latest.region}")
        print(f"  Version: {latest.version}")
        print(f"  Filename: {latest.filename}")
        if latest.size:
            print(f"  Size: {latest.size / (1024**3):.2f} GB")

        download_url = downloader.get_download_url(latest)
        if download_url:
            print(f"  Download URL: {download_url}")
    else:
        print("\n✗ No Samsung firmware found via FUS API")

    # Interactive download
    print("\n" + "=" * 70)
    print("DOWNLOAD OPTIONS")
    print("=" * 70)

    print("\nRecommended approach for your QEMU/KVM virtual device:")
    print("1. Try Cuttlefish boot.img first (designed for virtual devices)")
    print("2. If that doesn't work, try GKI boot.img")
    print("3. Samsung firmware requires extraction (large download)")

    print("\nQuick download commands:")
    print("\n# Option 1: Cuttlefish Android 13 (RECOMMENDED)")
    print("curl -L -o boot_cuttlefish_android13.img \\")
    print(f"  '{cuttlefish_images['cuttlefish_android13']['url']}'")

    print("\n# Option 2: Latest Cuttlefish")
    print("curl -L -o boot_cuttlefish_latest.img \\")
    print(f"  '{cuttlefish_images['cuttlefish_latest']['url']}'")

    print("\n# Option 3: GKI Android 13")
    print("curl -L -o boot_gki_android13.img \\")
    print(f"  '{gki_images['gki_android13']['url']}'")

    # Offer to download
    try:
        choice = input("\n\nDownload now? (1=Cuttlefish A13, 2=Cuttlefish Latest, 3=GKI, n=No): ").strip()

        if choice == '1':
            output_path = output_dir / "boot_cuttlefish_android13.img"
            download_file(cuttlefish_images['cuttlefish_android13']['url'], str(output_path))
        elif choice == '2':
            output_path = output_dir / "boot_cuttlefish_latest.img"
            download_file(cuttlefish_images['cuttlefish_latest']['url'], str(output_path))
        elif choice == '3':
            output_path = output_dir / "boot_gki_android13.img"
            download_file(gki_images['gki_android13']['url'], str(output_path))
        else:
            print("\nNo download selected. Use curl commands above to download manually.")

    except KeyboardInterrupt:
        print("\n\nCancelled by user.")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. Download a boot.img using one of the methods above
2. Patch it with Magisk:
   - Open Magisk app on device
   - Tap 'Install' → 'Select and Patch a File'
   - Choose the downloaded boot.img
   - Magisk will create magisk_patched_*.img

3. Flash the patched boot.img:
   adb push /path/to/magisk_patched_*.img /sdcard/

4. Find the boot partition and flash:
   adb shell su -c "dd if=/sdcard/magisk_patched_*.img of=/dev/block/bootdevice/by-name/boot"

Note: For virtual devices, you may need to modify the VM configuration
to use the patched boot image instead of flashing via dd.
""")

if __name__ == "__main__":
    main()
