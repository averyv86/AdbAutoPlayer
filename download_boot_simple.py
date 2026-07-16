#!/usr/bin/env python3
"""
Simple Boot Image Downloader for SM-S908E Virtual Device
Downloads Cuttlefish boot.img (optimized for QEMU/KVM)
"""

import requests
import sys
from pathlib import Path

# Boot image sources (ordered by recommendation)
BOOT_IMAGES = {
    'cuttlefish_android13_arm64': {
        'url': 'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img',
        'filename': 'boot_cuttlefish_android13_arm64.img',
        'description': 'Cuttlefish Android 13 ARM64 (RECOMMENDED)',
        'reason': 'Matches your Android 13 version and QEMU/KVM architecture'
    },
    'cuttlefish_latest_arm64': {
        'url': 'https://ci.android.com/builds/latest/branches/aosp-main/targets/aosp_cf_arm64-trunk_staging-userdebug/view/boot.img',
        'filename': 'boot_cuttlefish_latest_arm64.img',
        'description': 'Latest Cuttlefish ARM64',
        'reason': 'Newest features but may be unstable'
    },
    'generic_system_image': {
        'url': 'https://dl.google.com/android/repository/sys-img/google_apis/arm64-v8a-33_r10.zip',
        'filename': 'generic_system_image.zip',
        'description': 'Generic System Image Android 13 (API 33)',
        'reason': 'Official Google generic image (requires extraction)',
        'extract': True
    }
}

def download_boot_image(source_key: str, output_dir: Path) -> bool:
    """Download boot image from specified source"""

    if source_key not in BOOT_IMAGES:
        print(f"❌ Unknown source: {source_key}")
        print(f"Available: {', '.join(BOOT_IMAGES.keys())}")
        return False

    source = BOOT_IMAGES[source_key]
    output_path = output_dir / source['filename']

    print(f"\n{'='*70}")
    print(f"📥 Downloading: {source['description']}")
    print(f"{'='*70}")
    print(f"URL: {source['url']}")
    print(f"Output: {output_path}")
    print(f"Reason: {source['reason']}")
    print()

    try:
        response = requests.get(source['url'], stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            downloaded = 0
            chunk_size = 8192

            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)

                        bar_length = 50
                        filled_length = int(bar_length * downloaded // total_size)
                        bar = '█' * filled_length + '-' * (bar_length - filled_length)

                        print(f'\r  [{bar}] {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)', end='')

        print(f"\n\n✅ Success! Downloaded to: {output_path}")
        print(f"   Size: {output_path.stat().st_size / (1024*1024):.2f} MB")

        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("SM-S908E Boot Image Downloader for Virtual Device")
    print("="*70)

    output_dir = Path("./boot_images")
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {output_dir.absolute()}\n")

    # Show available options
    print("Available boot images:\n")
    for i, (key, info) in enumerate(BOOT_IMAGES.items(), 1):
        marker = "⭐" if i == 1 else "  "
        print(f"{marker} {i}. {info['description']}")
        print(f"    {info['reason']}")
        print()

    # Auto-download recommended image
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("🚀 Auto-downloading recommended image (Cuttlefish Android 13)...")
        recommended_key = list(BOOT_IMAGES.keys())[0]
        success = download_boot_image(recommended_key, output_dir)

        if success:
            print("\n" + "="*70)
            print("NEXT STEPS")
            print("="*70)
            print_next_steps(output_dir / BOOT_IMAGES[recommended_key]['filename'])

        return 0 if success else 1

    # Interactive mode
    try:
        choice = input("Select option (1-3, or q to quit): ").strip()

        if choice.lower() == 'q':
            print("Cancelled.")
            return 0

        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(BOOT_IMAGES):
                print("❌ Invalid choice")
                return 1

            selected_key = list(BOOT_IMAGES.keys())[choice_idx]
            success = download_boot_image(selected_key, output_dir)

            if success:
                print("\n" + "="*70)
                print("NEXT STEPS")
                print("="*70)
                print_next_steps(output_dir / BOOT_IMAGES[selected_key]['filename'])

            return 0 if success else 1

        except ValueError:
            print("❌ Please enter a number")
            return 1

    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        return 0

def print_next_steps(boot_img_path: Path):
    """Print instructions for using the downloaded boot.img"""

    print(f"""
📱 Using the boot.img with Magisk:

1. Transfer boot.img to device:
   adb push {boot_img_path} /sdcard/Download/boot.img

2. Patch with Magisk app:
   - Open Magisk app on your device
   - Tap "Install" button
   - Select "Select and Patch a File"
   - Navigate to /sdcard/Download/boot.img
   - Tap "Let's Go"
   - Wait for patching to complete
   - Magisk will create: /sdcard/Download/magisk_patched_[random].img

3. Pull the patched image:
   adb pull /sdcard/Download/magisk_patched_*.img ./

4. For QEMU/KVM virtual device:

   Option A - Flash to boot partition (if accessible):
   adb push magisk_patched_*.img /sdcard/
   adb shell su -c "dd if=/sdcard/magisk_patched_*.img of=/dev/block/by-name/boot"
   adb reboot

   Option B - Modify VM boot configuration:
   - Shutdown the VM
   - Replace the boot.img in VM configuration with patched image
   - Restart the VM

   Option C - Use fastboot (if available):
   adb reboot bootloader
   fastboot flash boot magisk_patched_*.img
   fastboot reboot

⚠️  IMPORTANT FOR VIRTUAL DEVICES:
Since you're running on QEMU/KVM (vda/vdb), the standard Android boot
partition may not be accessible. You may need to:

1. Check your VM configuration files for boot image location
2. Replace the boot.img in the VM's storage configuration
3. Or use the VM's management interface to update the boot image

Your device shows:
- ro.secure=0 (security disabled)
- ro.debuggable=1 (debugging enabled)
- Block devices: vda, vdb (virtio, not standard Android partitions)

This suggests you need to modify the VM configuration rather than
flashing via Android commands.

🔧 Alternative approach - Check VM configuration:
cat /proc/cmdline  # Shows kernel boot parameters
ls -la /dev/block/  # Shows available block devices
""")

if __name__ == "__main__":
    sys.exit(main())
