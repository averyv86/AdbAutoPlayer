=== Prebuilt Kernel & DTB Files ===

You MUST obtain these files from a stock firmware image
for Samsung SM-X110 (gta9wifi) to build TWRP.

How to get them:

Option A: Extract from stock firmware (recommended)
  1. Download stock firmware from samfw.com or similar
  2. Extract the AP tar.md5 file
  3. You'll find boot.img and dtbo.img inside
  4. Use unpackbootimg to extract kernel from boot.img:
     unpackbootimg -i boot.img -o boot_extracted/
  5. The kernel will be: boot_extracted/boot.img-kernel
  6. Rename it to "kernel" and place in this directory

Option B: Extract from running device (requires root)
  1. adb shell
  2. su
  3. dd if=/dev/block/by-name/boot of=/sdcard/boot.img
  4. adb pull /sdcard/boot.img
  5. Use unpackbootimg to extract

Files needed in this directory:
  - kernel          (Linux kernel zImage/Image from boot.img)
  - dtb.img         (Device tree blob from boot.img or vendor_boot.img)
  - dtbo.img        (Device tree blob overlay from dtbo partition)

Size reference:
  - kernel:   ~25-35 MB
  - dtb.img:  ~1-2 MB
  - dtbo.img: ~256-512 KB
