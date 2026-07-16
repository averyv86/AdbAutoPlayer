# TWRP for Samsung Galaxy Tab A9 (SM-X110 / gta9wifi)

**Device**: Samsung Galaxy Tab A9 WiFi  
**Model**: SM-X110  
**Codename**: gta9wifi  
**SoC**: MediaTek MT8781 (MT6789)  
**Android**: 12 (kernel 5.10)

## What's in this package

```
twrp_gta9wifi_build_package/
├── README.md                       # THIS FILE — build instructions
├── device_tree/                    # TWRP device tree (drop into AOSP source)
│   ├── Android.mk                  # Build inclusion
│   ├── AndroidProducts.mk          # Lunch targets
│   ├── BoardConfig.mk              # Board configuration (fixed, no duplicates)
│   ├── device.mk                   # Product definition (REVISED)
│   ├── omni_gta9wifi.mk            # OmniROM-style product mk
│   ├── twrp_gta9wifi.mk            # TWRP-specific product mk (NEW)
│   ├── vendorsetup.sh              # Lunch combos
│   ├── prebuilt/
│   │   ├── README_prebuilt.txt     # How to get kernel + dtb
│   ├── recovery/root/
│   │   ├── init.recovery.mt8781.rc    # MediaTek init (USB config)
│   │   ├── init.recovery.samsung.rc   # Samsung init (EFS, battery)
│   │   ├── dsms.rc                    # DSMS
│   │   ├── dsms_common.rc             # DSMS common
│   │   ├── mtk-plpath-utils.rc        # MediaTek PL path service
│   │   └── system/etc/
│   │       └── recovery.fstab         # Full partition table (52 entries)
├── build_twrp_gta9wifi.sh          # ONE-CLICK BUILD SCRIPT
└── CITATION.cff                    # Citation metadata
```

## Build Methods

### Method 1: Google Colab (easiest — no local setup)

Run this cell by cell in a **Google Colab** notebook:

```python
# Cell 1: Mount Drive and set up
!apt-get update -qq && apt-get install -y -qq bc bison build-essential ccache curl flex git gnupg gperf \
  lib32ncurses5-dev lib32readline-dev lib32z1-dev liblz4-tool libncurses5 libncurses5-dev \
  libsdl1.2-dev libssl-dev libxml2 libxml2-utils lz4 lzop pngcrush rsync schedtool \
  squashfs-tools xsltproc zip zlib1g-dev python3 python3-pip openjdk-11-jdk \
  android-sdk-libsparse-utils erofs-utils device-tree-compiler -qq

# Cell 2: Install repo
!mkdir -p ~/bin && curl -s https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo && chmod a+x ~/bin/repo
import os
os.environ['PATH'] += f":{os.path.expanduser('~/bin')}"

# Cell 3: Clone device tree into working dir
!mkdir -p ~/twrp/device/samsung
!git clone https://github.com/YOUR_USERNAME/twrp_device_samsung_gta9wifi ~/twrp/device/samsung/gta9wifi  # REPLACE with your repo
# OR: upload device_tree/ folder manually via Colab file upload

# Cell 4: Init TWRP source
%cd ~/twrp
!repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-12.1

# Cell 5: Sync (takes ~30 min)
!repo sync -c --no-clone-bundle --no-tags -j4 2>&1 | tail -10

# Cell 6: Build
!source build/envsetup.sh && lunch twrp_gta9wifi-eng && mka recoveryimage -j4 2>&1 | tail -20
```

After build completes, the recovery image is at:  
`~/twrp/out/target/product/gta9wifi/recovery.img`

Download it from Colab → right-click file → Download.

### Method 2: Ubuntu/Linux (native or WSL2)

**Requirements:** Ubuntu 20.04+, 120GB+ free space, 8GB+ RAM, fast internet.

```bash
# Install dependencies
sudo apt update && sudo apt install -y bc bison build-essential ccache curl flex g++-multilib \
  gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-dev lib32z1-dev liblz4-tool \
  libncurses5 libncurses5-dev libsdl1.2-dev libssl-dev libxml2 libxml2-utils lz4 lzop pngcrush \
  rsync schedtool squashfs-tools xsltproc zip zlib1g-dev python3 python3-pip openjdk-11-jdk \
  android-sdk-libsparse-utils erofs-utils device-tree-compiler

# Install repo
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH="$HOME/bin:$PATH"

# Create build directory
mkdir -p ~/twrp_build/device/samsung
cd ~/twrp_build

# Copy device tree
cp -r /path/to/device_tree/ ./device/samsung/gta9wifi/

# Init repo
repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-12.1

# Sync
repo sync -c --no-clone-bundle --no-tags -j$(nproc)

# Build
source build/envsetup.sh
lunch twrp_gta9wifi-eng
mka recoveryimage -j$(nproc)
```

Output: `~/twrp_build/out/target/product/gta9wifi/recovery.img`

### Method 3: Use the included build script

```bash
chmod +x build_twrp_gta9wifi.sh
./build_twrp_gta9wifi.sh
```

## Getting the Kernel & DTB

Before building, you need `kernel`, `dtb.img`, and `dtbo.img` in `device_tree/prebuilt/`.

**From stock firmware (recommended):**
1. Download SM-X110 firmware from [SamFW](https://samfw.com)
2. Extract the `.tar.md5` file
3. Inside you'll find `boot.img` and `dtbo.img`
4. Install `unpackbootimg` and run:
   ```bash
   unpackbootimg -i boot.img -o boot_extracted/
   ```
5. Copy files:
   ```bash
   cp boot_extracted/boot.img-kernel device_tree/prebuilt/kernel
   cp boot_extracted/boot.img-dtb device_tree/prebuilt/dtb.img
   cp dtbo.img device_tree/prebuilt/dtbo.img
   ```

**From device (requires root):**
```bash
adb shell
su
dd if=/dev/block/by-name/boot of=/sdcard/boot.img
dd if=/dev/block/by-name/dtbo of=/sdcard/dtbo.img
exit
adb pull /sdcard/boot.img
adb pull /sdcard/dtbo.img
unpackbootimg -i boot.img -o boot_extracted/
cp boot_extracted/boot.img-kernel device_tree/prebuilt/kernel
cp boot_extracted/boot.img-dtb device_tree/prebuilt/dtb.img
```

## Flashing

### Via Odin (Windows)
1. Open **Odin3 v3.14+**
2. Click **AP** and select `recovery.img`
3. **UNCHECK** "Auto Reboot" in Options
4. Put device in **Download Mode**: Power off → hold Volume Up + Volume Down → plug USB
5. Click **Start**
6. After flash completes: **Hold Volume Up + Power** to boot recovery immediately (otherwise stock recovery overwrites it)

### Via fastboot (if bootloader unlocked)
```bash
fastboot flash recovery recovery.img
fastboot reboot
```

### Via Heimy (cross-platform)
```bash
heimdall flash --RECOVERY recovery.img --no-reboot
```

## Enabling Fastbootd Mode

If you need fastbootd (not just TWRP), use the `patch-recovery-revived` tool you already have:

```bash
# From the patch-recovery-revived folder
./patch-recovery.sh /path/to/recovery.img SM-X110
```

This will hex-patch the recovery binary and produce an Odin-flashable `.tar` with fastbootd support.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `BOARD_SAMSUNG_DYNAMIC_PARTITIONS_SIZE` mismatch | Check with: `lpdump super.img | grep "Dynamic partition"` and update BoardConfig.mk |
| Recovery boots but touch doesn't work | Try different `TW_THEME` (`landscape_hdpi` for tablet), adjust `TW_Y_OFFSET` |
| "No such device" during build | Ensure `lunch` target is correct: `twrp_gta9wifi-eng` |
| USB/ADB not working in recovery | Check `init.recovery.mt8781.rc` for `musb-hdrc` controller name |
| AVB error when flashing | Disable `BOARD_AVB_ENABLE` in BoardConfig.mk and rebuild |

## Credits

- Device tree based on SebaUbuntu's TWRP device tree generator
- Kernel source: Samsung Open Source
- TWRP source: https://github.com/minimal-manifest-twrp
