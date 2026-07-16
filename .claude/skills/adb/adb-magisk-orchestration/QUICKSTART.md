# Magisk Installation Orchestrator - Quick Start Guide

Get started with the Magisk Installation Orchestrator in 5 minutes.

## Prerequisites

### 1. Device Requirements
- ✅ Android device with **unlocked bootloader**
- ✅ **Root access** available (for boot extraction)
- ✅ **Developer mode** enabled
- ✅ **USB debugging** enabled
- ✅ At least **2GB free storage**

### 2. System Requirements
- ✅ Python 3.12+
- ✅ ADB installed and in PATH
- ✅ Fastboot installed and in PATH (for flashing)
- ✅ Tesseract OCR installed (for verification)

### 3. Verify Installation
```bash
# Check ADB
adb version
# Should show: Android Debug Bridge version 1.0.41+

# Check Fastboot
fastboot --version
# Should show: fastboot version ...

# Check Tesseract
tesseract --version
# Should show: tesseract 5.x.x

# Check Python
python3 --version
# Should show: Python 3.12.x or higher
```

## Quick Installation

### Option 1: One-Line Installation (Recommended)

```python
from adb_magisk_orchestrator import MagiskOrchestrator
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper

# Connect and install
device = AdbDeviceWrapper.create_from_settings()
orchestrator = MagiskOrchestrator.quick_install(device)
```

### Option 2: Standard Installation

```python
from adb_magisk_orchestrator import MagiskOrchestrator
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_ui_navigator import UINavigator
from adb_ocr_finder import OCRTextFinder

# 1. Connect to device
device = AdbDeviceWrapper.create_from_settings()

# 2. Setup helpers
ocr_finder = OCRTextFinder(device)
ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

# 3. Create orchestrator
orchestrator = MagiskOrchestrator(
    device=device,
    ui_navigator=ui_navigator,
    ocr_finder=ocr_finder
)

# 4. Execute installation
result = orchestrator.execute_installation(magisk_version="latest")

# 5. Check results
if result.success:
    print(f"✅ Installed Magisk {result.magisk_version}")
else:
    print(f"❌ Failed: {result.error}")
```

### Option 3: Command Line

```bash
# Run standalone
python adb_magisk_orchestrator.py

# Or with example runner
python example_usage.py
```

## Common Use Cases

### 1. Install Latest Version
```python
result = orchestrator.execute_installation(magisk_version="latest")
```

### 2. Install Specific Version
```python
result = orchestrator.execute_installation(magisk_version="30.6")
```

### 3. Resume Failed Installation
```python
# If failed at phase 4, skip phases 1-3
result = orchestrator.execute_installation(
    magisk_version="30.6",
    skip_phases=[1, 2, 3]
)
```

### 4. Custom Working Directory
```python
orchestrator = MagiskOrchestrator(
    device=device,
    ui_navigator=ui_navigator,
    ocr_finder=ocr_finder,
    work_dir="/custom/path/magisk"
)
```

## Troubleshooting

### Problem: "Device not found"
```bash
# Solution 1: Check ADB connection
adb devices
# Should show: 127.0.0.1:5555    device

# Solution 2: Restart ADB server
adb kill-server
adb start-server

# Solution 3: Reconnect device
adb connect 127.0.0.1:5555
```

### Problem: "Download failed"
```python
# Solution: Check network and retry with specific version
result = orchestrator.execute_installation(magisk_version="30.6")
```

### Problem: "Installation failed at Phase 3 (Extract)"
```bash
# Solution: Verify root access
adb shell su -c "id"
# Should show: uid=0(root) ...

# If not rooted, install temporary root solution first
```

### Problem: "OCR text not found"
```python
# Solution 1: Adjust confidence threshold
from adb_auto_player.models import ConfidenceValue
ocr_finder = OCRTextFinder(device, min_confidence=ConfidenceValue(0.5))

# Solution 2: Use fallback without OCR
orchestrator.ocr_finder = None  # Will use package manager check
```

### Problem: "Flash failed"
```bash
# Solution 1: Check bootloader unlocked
fastboot oem device-info
# Should show: Device unlocked: true

# Solution 2: Test fastboot connection
adb reboot bootloader
fastboot devices
# Should show device serial

# Solution 3: Reboot back to system
fastboot reboot
```

## Verification

### Check Installation Success
```python
if result.success:
    print(f"✅ Success!")
    print(f"Version: {result.magisk_version}")
    print(f"Duration: {result.total_duration:.1f}s")
    print(f"Phases: {len(result.phases)}/7 completed")

    # Check each phase
    for phase in result.phases:
        print(f"Phase {phase.phase_number}: {phase.phase_name} - {'✅' if phase.success else '❌'}")
```

### Verify on Device
```bash
# 1. Check Magisk app installed
adb shell pm list packages | grep magisk
# Should show: package:com.topjohnwu.magisk

# 2. Check root access
adb shell su -c "magisk -v"
# Should show version: 30.6:30600

# 3. Check Zygisk enabled
adb shell su -c "magisk --denylist status"
# Should show: Enforce DenyList: true
```

## Next Steps

### 1. Install Modules
```bash
# Use Magisk Manager UI or command line
adb push module.zip /sdcard/Download/
adb shell su -c "magisk --install-module /sdcard/Download/module.zip"
```

### 2. Configure Zygisk
- Open Magisk Manager app
- Go to Settings
- Configure DenyList
- Hide Magisk if needed

### 3. Verify SafetyNet
- Install SafetyNet checker app
- Run test
- Should pass basicIntegrity and ctsProfile

### 4. Install PlayIntegrityFix (Optional)
```python
# Use module installation script
from adb_magisk_module_installer import install_module
install_module(device, "playintegrity-fix")
```

## Performance Tips

### 1. Speed Up Download
```python
# Use local cache if available
orchestrator.work_dir = "/path/to/cached/files"
result = orchestrator.execute_installation(skip_phases=[1])  # Skip download
```

### 2. Reduce Retries
```python
# If stable connection, reduce retry overhead
orchestrator.MAX_RETRIES = 1
```

### 3. Increase Timeouts
```python
# If slow device, increase timeouts
orchestrator.TIMEOUT_DEFAULT = 60  # Default: 30s
```

### 4. Parallel Operations
```python
# Download and install in parallel (future enhancement)
# Currently sequential for reliability
```

## Best Practices

### 1. Always Backup
```bash
# Backup boot partition before installation
adb shell su -c "dd if=/dev/block/by-name/boot of=/sdcard/boot_backup.img"
adb pull /sdcard/boot_backup.img ./boot_backup.img
```

### 2. Test on Development Device
- Test full workflow on non-production device first
- Verify all phases complete successfully
- Check for any device-specific issues

### 3. Monitor Logs
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("magisk_install.log"),
        logging.StreamHandler()
    ]
)
```

### 4. Handle Interruptions
```python
try:
    result = orchestrator.execute_installation()
except KeyboardInterrupt:
    print("⚠️  Installation interrupted")
    print("Resume with: skip_phases=[completed_phases]")
```

## Support

### Get Help
1. Check [README.md](README.md) for detailed documentation
2. Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture
3. Run [example_usage.py](example_usage.py) for working examples
4. Check logs in `/tmp/magisk/` for error details

### Report Issues
Include:
- Device model and Android version
- ADB/Fastboot versions
- Full error message and logs
- Phase where failure occurred
- Steps to reproduce

## Complete Example

```python
#!/usr/bin/env python3
"""Complete Magisk installation example."""

import logging
from pathlib import Path
from adb_magisk_orchestrator import MagiskOrchestrator
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_ui_navigator import UINavigator
from adb_ocr_finder import OCRTextFinder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("magisk_install.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main installation flow."""
    try:
        # 1. Connect to device
        logger.info("Connecting to device...")
        device = AdbDeviceWrapper.create_from_settings()
        logger.info(f"✅ Connected: {device.serial}")

        # 2. Setup helpers
        logger.info("Initializing OCR and UI navigation...")
        ocr_finder = OCRTextFinder(device)
        ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

        # 3. Create orchestrator
        logger.info("Creating orchestrator...")
        orchestrator = MagiskOrchestrator(
            device=device,
            ui_navigator=ui_navigator,
            ocr_finder=ocr_finder,
            work_dir="/tmp/magisk"
        )

        # 4. Execute installation
        logger.info("Starting Magisk installation...")
        result = orchestrator.execute_installation(magisk_version="latest")

        # 5. Display results
        if result.success:
            logger.info(f"✅ Installation Successful!")
            logger.info(f"   Version: {result.magisk_version}")
            logger.info(f"   Duration: {result.total_duration:.1f}s")
            logger.info(f"   Phases: {len(result.phases)}/7 completed")
            return 0
        else:
            logger.error(f"❌ Installation Failed: {result.error}")
            for phase in result.phases:
                if not phase.success:
                    logger.error(f"   Failed at Phase {phase.phase_number}: {phase.phase_name}")
                    logger.error(f"   Error: {phase.error}")
            return 1

    except KeyboardInterrupt:
        logger.warning("⚠️  Installation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

## What's Next?

1. **Install Modules**: Use Magisk Manager to install modules
2. **Configure Zygisk**: Set up app hiding and DenyList
3. **Verify SafetyNet**: Test device integrity status
4. **Install PlayIntegrityFix**: Bypass Play Integrity checks (optional)
5. **Customize Settings**: Configure Magisk to your needs

---

**Version**: 1.0.0
**Author**: MoAI-ADK
**Last Updated**: 2025-12-02

For detailed information, see [README.md](README.md)
