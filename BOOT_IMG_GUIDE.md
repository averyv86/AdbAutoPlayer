# Boot Image Guide for SM-S908E Virtual Device

## 🎯 Quick Start

Your Samsung SM-S908E is running as a **QEMU/KVM virtual device** with:
- Android 13 (API 33)
- ARM64 architecture
- Virtio block devices (vda/vdb)
- Magisk installed but not rooted

## 📥 Download Boot Image

### Option 1: Simple Python Script (Recommended)

```bash
# Auto-download the recommended boot.img
python3 download_boot_simple.py --auto

# Or interactive mode
python3 download_boot_simple.py
```

### Option 2: Comprehensive Search

```bash
# Search all sources and show detailed info
python3 get_boot_img.py
```

### Option 3: Direct Download (curl)

```bash
# Download Cuttlefish Android 13 (best match for your device)
curl -L -o boot.img \
  'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img'
```

See `boot_img_urls.txt` for all available URLs.

## 🔧 Patch Boot Image with Magisk

### Step 1: Transfer boot.img to device

```bash
adb push boot.img /sdcard/Download/boot.img
```

### Step 2: Patch with Magisk app

1. Open Magisk app on the device
2. Tap "Install" button (top right)
3. Select "Select and Patch a File"
4. Navigate to `/sdcard/Download/boot.img`
5. Tap "Let's Go"
6. Wait for patching to complete (30-60 seconds)
7. Magisk creates: `/sdcard/Download/magisk_patched_[random].img`

### Step 3: Retrieve patched image

```bash
# Pull the patched image back to your computer
adb pull /sdcard/Download/magisk_patched_*.img ./magisk_patched.img
```

## 🚀 Flash Boot Image

### ⚠️ IMPORTANT: Virtual Device Considerations

Your device runs on QEMU/KVM, so standard Android flashing may not work.

### Method A: Check Block Devices First

```bash
# Check available partitions
adb shell cat /proc/partitions

# Check kernel boot parameters
adb shell cat /proc/cmdline

# List block devices
adb shell ls -la /dev/block/
```

### Method B: Try Standard Flash (may not work)

```bash
# Push patched image
adb push magisk_patched.img /sdcard/

# Attempt to flash (requires root or special permissions)
adb shell su -c "dd if=/sdcard/magisk_patched.img of=/dev/block/by-name/boot"

# Or try virtio devices directly
adb shell su -c "dd if=/sdcard/magisk_patched.img of=/dev/vda1"
# (replace vda1 with correct partition - check /proc/partitions first)

# Reboot
adb reboot
```

### Method C: Modify VM Configuration (Likely Required)

Since your device shows `virtio` block devices instead of standard Android partitions, you probably need to:

1. **Locate VM configuration file**
   - Check your VM manager (libvirt, QEMU, Android Studio AVD, etc.)
   - Find where boot.img is referenced

2. **Replace boot.img in VM config**
   ```bash
   # Example for libvirt/QEMU
   virsh dumpxml <vm-name> > vm-config.xml
   # Edit vm-config.xml to point to magisk_patched.img
   virsh define vm-config.xml
   ```

3. **Or rebuild VM with new boot image**
   - If using Android Studio AVD: Replace boot.img in system-images folder
   - If using custom QEMU: Update -kernel or -drive parameters

### Method D: Fastboot (if available)

```bash
# Check if fastboot is accessible
adb reboot bootloader

# Flash boot partition
fastboot flash boot magisk_patched.img

# Reboot
fastboot reboot
```

## 🔍 Troubleshooting

### "adb root" doesn't work

The issue you're experiencing (`adb root` says restarting but shell remains uid=2000) is expected because:
- `ro.secure=0` only allows `adb root` to attempt restart
- Without proper boot.img, root privileges aren't actually granted
- This is why you need to patch and flash boot.img

### Can't find boot partition

```bash
# Search for boot-related partitions
adb shell find /dev/block -name "*boot*"

# Check partition table
adb shell cat /proc/partitions

# Check device mapper
adb shell ls -la /dev/mapper/
```

### Virtual device specifics

For QEMU/KVM virtual devices:

1. **Check VM disk layout**
   ```bash
   # On the host system (not in adb shell)
   qemu-img info <vm-disk-image>
   ```

2. **Boot image might be embedded in disk image**
   - Extract current disk image
   - Use tools like `simg2img` or `ext4` tools to extract boot partition
   - Replace with patched version
   - Rebuild disk image

3. **Alternative: Use Magisk in recovery mode**
   - Boot into recovery (if available)
   - Flash magisk_patched.img as boot image from recovery
   - Or use Magisk's "Direct Install" method

## 📚 Files Included

- `download_boot_simple.py` - Simple interactive downloader
- `get_boot_img.py` - Comprehensive boot image finder (Samsung FUS API + generic sources)
- `boot_img_urls.txt` - Direct download URLs and curl commands
- `BOOT_IMG_GUIDE.md` - This guide

## 🔗 Resources

- **Cuttlefish (Google's QEMU/KVM Android)**: https://source.android.com/docs/setup/create/cuttlefish
- **Magisk Documentation**: https://topjohnwu.github.io/Magisk/
- **GKI (Generic Kernel Image)**: https://source.android.com/docs/core/architecture/kernel/generic-kernel-image
- **Android CI/CD Builds**: https://ci.android.com/

## ⚡ Quick Reference

### Download boot.img
```bash
python3 download_boot_simple.py --auto
```

### Patch with Magisk
```bash
adb push boot.img /sdcard/Download/boot.img
# Open Magisk app → Install → Select and Patch a File → boot.img
adb pull /sdcard/Download/magisk_patched_*.img ./
```

### Check device info
```bash
adb shell cat /proc/partitions
adb shell cat /proc/cmdline
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
```

### Verify root after flashing
```bash
adb shell su -c "id"
# Expected: uid=0(root) gid=0(root)

adb shell magisk -v
# Expected: Magisk version number
```

## 💡 Notes

1. **Cuttlefish images are recommended** because they're specifically designed for QEMU/KVM virtual devices like yours.

2. **Your device characteristics** suggest it's running in a virtualized environment (virtio drivers, non-standard partition layout).

3. **Standard Android flashing procedures may not work** - you may need to modify the underlying VM configuration.

4. **Check with your VM provider** - if this is from a cloud service or specific emulator, consult their documentation for root/custom boot image procedures.

5. **Backup first** - make a snapshot of your VM before attempting to flash boot images.

## 🆘 Still Having Issues?

If none of these methods work, your virtual device may have additional restrictions:

1. **Check if it's a managed VM** (cloud provider, corporate environment)
2. **Look for VM-specific rooting guides** for your specific platform
3. **Consider using a local Android emulator** (Android Studio AVD) where you have full control
4. **Try Magisk's "Direct Install to inactive slot"** if your device supports A/B partitioning

For more help, provide:
- Output of `adb shell cat /proc/cmdline`
- Output of `adb shell cat /proc/partitions`
- Your VM platform/provider (QEMU, libvirt, Android Studio, cloud provider, etc.)
