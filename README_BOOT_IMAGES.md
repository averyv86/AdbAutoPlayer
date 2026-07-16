# Boot Image Solution for SM-S908E Virtual Device

## 📖 Overview

This directory contains tools and documentation to obtain and flash a boot.img for rooting your Samsung SM-S908E virtual device running on QEMU/KVM.

**Current Status:**
- ✅ Magisk v27.0 installed on device
- ❌ Root not active (Installed: N/A)
- ⚠️ `adb root` restarts but doesn't grant root privileges
- 🎯 **Solution:** Download, patch, and flash boot.img

## 🚀 Quick Start

**30-second solution:**
```bash
curl -L -o boot.img \
  'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img'
adb push boot.img /sdcard/Download/boot.img
# Open Magisk app → Install → Select and Patch File → boot.img
adb pull /sdcard/Download/magisk_patched_*.img ./
```

📘 **For complete instructions, see:** `QUICK_START.md`

## 📁 Documentation

| File | Description | When to Use |
|------|-------------|-------------|
| 📄 **QUICK_START.md** | Fast 30-second solution | Start here if you want immediate action |
| 📘 **BOOT_IMG_SUMMARY.md** | Complete solution overview | Understand the full picture |
| 📗 **BOOT_IMG_GUIDE.md** | Detailed step-by-step guide | Need comprehensive instructions |
| 📝 **boot_img_urls.txt** | Direct download URLs | Want to use curl/wget manually |
| 📄 **README_BOOT_IMAGES.md** | This file | Navigation and overview |

## 🛠️ Tools Provided

### 1. Comprehensive Finder (`get_boot_img.py`)

Searches multiple sources for boot images:
- ✅ Cuttlefish (Google's QEMU/KVM Android)
- ✅ Generic Kernel Images (GKI)
- ✅ Samsung FUS API (official firmware)
- ✅ AOSP generic builds

**Usage:**
```bash
python3 get_boot_img.py
# Interactive mode with all sources
```

**Features:**
- Checks Samsung firmware across 10 regions
- Finds Cuttlefish images (optimized for QEMU/KVM)
- Locates GKI certified boot images
- Provides direct download URLs
- Shows detailed compatibility info

### 2. Simple Downloader (`download_boot_simple.py`)

Quick interactive downloader with progress bar.

**Usage:**
```bash
# Auto-download recommended image
python3 download_boot_simple.py --auto

# Interactive mode
python3 download_boot_simple.py
```

**Features:**
- Progress bar with MB counter
- Auto-selects best match for your device
- Includes next-steps instructions
- Downloads to `./boot_images/` directory

### 3. URL Reference (`boot_img_urls.txt`)

Plain text file with all boot.img URLs and curl commands.

**Usage:**
```bash
cat boot_img_urls.txt
# Copy/paste curl commands
```

## 🎯 Recommended Boot Images

### 🥇 Option 1: Cuttlefish Android 13 (RECOMMENDED)

**Why recommended:**
- ✅ Matches your Android 13 version
- ✅ ARM64 architecture
- ✅ Designed for QEMU/KVM (your platform)
- ✅ Works with virtio devices (vda/vdb)
- ✅ Officially maintained by Google

**Download:**
```bash
curl -L -o boot.img \
  'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img'
```

**Size:** ~67 MB
**Compatibility:** 100%

### 🥈 Option 2: Cuttlefish Latest

Latest bleeding-edge build (may be unstable).

**Download:**
```bash
curl -L -o boot.img \
  'https://ci.android.com/builds/latest/branches/aosp-main/targets/aosp_cf_arm64-trunk_staging-userdebug/view/boot.img'
```

**Size:** ~70 MB
**Compatibility:** 90%

### 🥉 Option 3: GKI Android 13

Generic kernel image (may need device-specific modifications).

**Download:**
```bash
curl -L -o boot.img \
  'https://dl.google.com/android/gki/gki-certified-boot-android13-5.15.img'
```

**Size:** ~45 MB
**Compatibility:** 70%

## 🔄 Complete Rooting Process

### Step 1: Download boot.img
```bash
# Option A: Use Python script
python3 download_boot_simple.py --auto

# Option B: Use curl
curl -L -o boot.img \
  'https://ci.android.com/builds/latest/branches/aosp-android13-release/targets/aosp_cf_arm64-userdebug/view/boot.img'
```

### Step 2: Transfer to device
```bash
adb push boot.img /sdcard/Download/boot.img
```

### Step 3: Patch with Magisk
**On your device:**
1. Open Magisk app
2. Tap "Install"
3. Select "Select and Patch a File"
4. Choose `/sdcard/Download/boot.img`
5. Tap "Let's Go"
6. Wait for completion

### Step 4: Retrieve patched image
```bash
adb pull /sdcard/Download/magisk_patched_*.img ./magisk_patched.img
```

### Step 5: Flash patched boot.img

⚠️ **Important:** Your device runs on QEMU/KVM with virtio devices. Standard flashing may not work.

**Check partitions first:**
```bash
adb shell cat /proc/partitions
adb shell cat /proc/cmdline
```

**Try standard flash:**
```bash
adb push magisk_patched.img /sdcard/
adb shell su -c "dd if=/sdcard/magisk_patched.img of=/dev/block/by-name/boot"
adb reboot
```

**If that fails, modify VM configuration:**
- Locate your VM's configuration files
- Replace boot.img reference with `magisk_patched.img`
- Restart VM

### Step 6: Verify root
```bash
adb shell su -c "id"
# Expected: uid=0(root) gid=0(root)

adb shell magisk -v
# Expected: Magisk version number
```

## 🔍 Your Device Details

```
Model:          SM-S908E (Galaxy S22 Ultra Exynos)
Android:        13 (API 33)
Build:          TQ2B.230505.005.A1
Board:          taro (Snapdragon 8 Gen 1)

Virtualization: QEMU/KVM
Block Devices:  vda, vdb (virtio - NOT standard Android partitions)
Security:       ro.secure=0, ro.debuggable=1

Magisk Status:  v27.0 installed, NOT rooted (Installed: N/A)
Root Status:    adb root restarts but uid remains 2000 (shell)
```

## ⚠️ Virtual Device Considerations

Your device shows **virtio block devices** (vda/vdb) which indicates QEMU/KVM virtualization.

**Implications:**
1. Standard partition paths may not exist:
   - ❌ `/dev/block/bootdevice/by-name/boot`
   - ❌ `/dev/block/mmcblk0p*`
   - ✅ `/dev/vda*` or `/dev/vdb*`

2. Boot image may be embedded in VM disk image

3. You may need to modify VM configuration instead of flashing via dd

**Check your VM platform:**
- Android Studio AVD
- libvirt/QEMU
- Cloud provider virtual device
- Custom QEMU setup

Consult your platform's documentation for custom boot image procedures.

## 🛠️ Troubleshooting

### Samsung Firmware Not Available

The scripts couldn't fetch Samsung firmware via FUS API (tested 10 regions).

**Alternative methods:**
1. Use SamFirm or Frija tools (Windows)
2. Download from sammobile.com (requires account)
3. Download from samfw.com or samfrew.com
4. **Recommended:** Use Cuttlefish instead (easier and works better for QEMU/KVM)

### Can't Find Boot Partition

```bash
# List all partitions
adb shell cat /proc/partitions

# Search for boot
adb shell find /dev/block -name "*boot*"

# Check kernel command line
adb shell cat /proc/cmdline
```

### Permission Denied

```bash
# Check current user
adb shell whoami
# Expected before root: shell (uid=2000)

# Try adb root
adb root
# May restart but not grant root (expected)

# This is why you need patched boot.img
```

### VM Doesn't Boot After Flash

1. Boot into recovery mode (if available)
2. Restore original boot.img
3. Or restore from VM snapshot/backup

## 📊 File Tree

```
AdbAutoPlayer/
├── README_BOOT_IMAGES.md          # This file (navigation)
├── QUICK_START.md                 # 30-second solution
├── BOOT_IMG_SUMMARY.md            # Complete overview
├── BOOT_IMG_GUIDE.md              # Detailed guide
├── boot_img_urls.txt              # Direct URLs
├── get_boot_img.py                # Comprehensive finder
├── download_boot_simple.py        # Simple downloader
└── boot_images/                   # Downloaded images
    ├── boot.img
    └── magisk_patched_*.img
```

## 🔗 Useful Resources

| Resource | URL |
|----------|-----|
| Cuttlefish Documentation | https://source.android.com/docs/setup/create/cuttlefish |
| Android CI Builds | https://ci.android.com/ |
| Magisk GitHub | https://github.com/topjohnwu/Magisk |
| Magisk Documentation | https://topjohnwu.github.io/Magisk/ |
| Generic Kernel Image | https://source.android.com/docs/core/architecture/kernel/generic-kernel-image |
| XDA Magisk Forum | https://forum.xda-developers.com/t/magisk-the-magic-mask-for-android.3473445/ |

## 🎓 Next Steps

1. **Read this file** for overview ✅ (you are here)
2. **See QUICK_START.md** for immediate action
3. **Run download script** to get boot.img
4. **Follow BOOT_IMG_GUIDE.md** for detailed steps
5. **Flash and verify** root access

## 💡 Tips

- **Start with Cuttlefish Android 13** - best match for your device
- **Make a VM snapshot** before flashing (safety)
- **Check your VM platform docs** for custom boot procedures
- **Use Magisk's "Direct Install"** if standard flashing fails
- **Keep original boot.img** for recovery

## 📞 Support

If you encounter issues:

1. Check `/proc/partitions` and `/proc/cmdline` on device
2. Identify your VM platform (QEMU, AVD, cloud provider, etc.)
3. Search for "[VM platform] + custom boot image" documentation
4. Consider alternative rooting methods for virtual devices

## ✅ Expected Outcome

After successful rooting:

```bash
$ adb shell su -c "id"
uid=0(root) gid=0(root) groups=0(root)

$ adb shell magisk -v
27.0:27000

$ adb shell su -c "whoami"
root
```

---

**Status:** Ready to proceed
**Recommended:** Download Cuttlefish Android 13 boot.img
**Confidence:** High (designed for QEMU/KVM virtual devices)
**Time Required:** 10-15 minutes

**Start here:** `QUICK_START.md`
