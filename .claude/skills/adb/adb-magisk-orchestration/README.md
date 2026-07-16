# Magisk Installation Orchestrator

Complete 7-phase Magisk installation workflow orchestrator with comprehensive error handling and state verification.

## Overview

The `MagiskOrchestrator` class coordinates the entire Magisk installation process from APK download through Zygisk enablement. It implements a robust workflow with retry logic, state verification, and detailed logging.

## Features

- **7-Phase Workflow**: Complete installation automation
- **Retry Logic**: Automatic retry with configurable attempts (default: 3)
- **State Verification**: Validates success at each phase
- **Error Recovery**: Comprehensive error handling and recovery
- **Progress Tracking**: Detailed phase-by-phase results
- **Resume Capability**: Can skip completed phases
- **Logging**: Comprehensive logging of all operations

## Installation Phases

### Phase 1: Download Magisk APK
- Fetches latest or specific version from GitHub releases
- Supports resume capability
- Validates download integrity

### Phase 2: Install APK
- Installs APK via ADB with force reinstall
- Verifies installation via package manager
- Validates app launch capability

### Phase 3: Extract Boot Image
- Extracts boot.img from device partition
- Validates extraction via file size check
- Stores locally for patching

### Phase 4: Patch Boot Image
- Patches boot.img using Magisk app
- Uses UI automation for patching workflow
- Validates patched output

### Phase 5: Flash Boot Image
- Reboots device to fastboot mode
- Flashes patched boot.img via fastboot
- Reboots back to system

### Phase 6: Verify Installation
- Checks for "Installed: [version]" text via OCR
- Verifies Magisk app functionality
- Validates root access

### Phase 7: Enable Zygisk
- Navigates to Magisk settings
- Enables Zygisk toggle
- Handles reboot prompt if needed

## Usage

### Basic Usage

```python
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_ui_navigator import UINavigator
from adb_ocr_finder import OCRTextFinder
from adb_magisk_orchestrator import MagiskOrchestrator

# Initialize device and helpers
device = AdbDeviceWrapper.create_from_settings()
ocr_finder = OCRTextFinder(device)
ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

# Create orchestrator
orchestrator = MagiskOrchestrator(
    device=device,
    ui_navigator=ui_navigator,
    ocr_finder=ocr_finder,
    work_dir="/tmp/magisk"
)

# Execute complete installation
result = orchestrator.execute_installation(magisk_version="latest")

# Check results
if result.success:
    print(f"✅ Installation successful in {result.total_duration:.1f}s")
    print(f"Version: {result.magisk_version}")
else:
    print(f"❌ Installation failed: {result.error}")
    for phase in result.phases:
        if not phase.success:
            print(f"   Failed Phase: {phase.phase_name}")
            print(f"   Error: {phase.error}")
```

### Skip Completed Phases

```python
# Skip phases 1-2 if APK already installed
result = orchestrator.execute_installation(
    magisk_version="30.6",
    skip_phases=[1, 2]
)
```

### Standalone Execution

```bash
# Run orchestrator as standalone script
python adb_magisk_orchestrator.py
```

## API Reference

### MagiskOrchestrator

```python
class MagiskOrchestrator:
    def __init__(
        self,
        device: AdbDeviceWrapper,
        ui_navigator: UINavigator,
        state_verifier: Optional[StateVerifier] = None,
        ocr_finder: Optional[OCRTextFinder] = None,
        work_dir: str = "/tmp/magisk"
    )
```

**Parameters:**
- `device`: ADB device wrapper for shell commands
- `ui_navigator`: UI navigation helper for tap automation
- `state_verifier`: State verification helper (optional, auto-created)
- `ocr_finder`: OCR text finder for UI element detection
- `work_dir`: Working directory for downloads and temporary files

### execute_installation()

```python
def execute_installation(
    self,
    magisk_version: str = "latest",
    skip_phases: Optional[List[int]] = None
) -> InstallationResult
```

Execute complete Magisk installation workflow.

**Parameters:**
- `magisk_version`: Version to install ("latest" or specific like "30.6")
- `skip_phases`: Optional list of phase numbers to skip (1-7)

**Returns:**
- `InstallationResult` with complete workflow status

### InstallationResult

```python
@dataclass
class InstallationResult:
    success: bool
    device_id: str
    magisk_version: str
    total_duration: float
    phases: List[PhaseResult]
    error: Optional[str]
```

**Methods:**
- `get_phase(phase_number: int)`: Get specific phase result
- `all_phases_success()`: Check if all phases succeeded

### PhaseResult

```python
@dataclass
class PhaseResult:
    phase_number: int
    phase_name: str
    status: PhaseStatus
    start_time: float
    end_time: float
    duration: float
    error: Optional[str]
    retry_count: int
    data: Dict[str, Any]
```

## Error Handling

The orchestrator implements comprehensive error handling:

1. **Retry Logic**: Each phase retries up to 3 times on failure
2. **State Validation**: Validates preconditions before each phase
3. **Recovery**: Attempts recovery strategies before failing
4. **Detailed Errors**: Captures and logs detailed error messages
5. **Graceful Failure**: Stops at first unrecoverable error

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "APK file not found" | Phase 1 download failed | Check network, retry download |
| "App not detected after installation" | Phase 2 install failed | Check device permissions, storage |
| "Boot image not found" | Phase 3 extract failed | Check device root access, partition |
| "Patched boot not found" | Phase 4 patch failed | Check Magisk app functionality |
| "Flash failed" | Phase 5 flash failed | Check fastboot connection, bootloader |
| "'Installed' text not found" | Phase 6 verify failed | Check screen resolution, OCR config |
| "Zygisk not enabled" | Phase 7 enable failed | Check Magisk settings UI, navigation |

## Configuration

### Retry Settings

```python
# Configure retry behavior
MagiskOrchestrator.MAX_RETRIES = 5  # Default: 3
```

### Timeout Settings

```python
# Configure timeouts per phase
MagiskOrchestrator.TIMEOUT_DEFAULT = 60  # Default: 30 seconds
```

### Working Directory

```python
# Custom work directory
orchestrator = MagiskOrchestrator(
    device=device,
    ui_navigator=ui_navigator,
    ocr_finder=ocr_finder,
    work_dir="/custom/path/magisk"
)
```

## Dependencies

- `adb_auto_player.device.adb.adb_device`: ADB device wrapper
- `adb_ui_navigator`: UI navigation framework
- `adb_ocr_finder`: OCR text detection
- `subprocess`: For calling phase scripts
- `pathlib`: Path handling
- `logging`: Logging framework

## Script Dependencies

The orchestrator calls these phase-specific scripts:

1. `adb-magisk-download.py` - Download Magisk APK
2. `adb-magisk-install-app.py` - Install APK via ADB
3. `adb-magisk-extract-boot.py` - Extract boot image
4. `adb-magisk-patch-boot.py` - Patch boot image
5. `adb-magisk-flash-boot.py` - Flash patched boot
6. `adb-magisk-enable-zygisk.py` - Enable Zygisk

All scripts must be available in `.claude/skills/adb/` hierarchy.

## Logging

The orchestrator provides detailed logging:

```
======================================================================
🚀 Starting Magisk Installation Workflow
   Device: 127.0.0.1:5555
   Version: latest
   Work Dir: /tmp/magisk
======================================================================
📥 Phase 1: Downloading Magisk latest
✅ Phase 1 Complete: Downloaded /tmp/magisk/Magisk-v30.6.apk
📦 Phase 2: Installing Magisk APK
✅ Phase 2 Complete: Magisk APK installed
💾 Phase 3: Extracting boot.img
✅ Phase 3 Complete: Extracted /tmp/magisk/boot.img
🔧 Phase 4: Patching boot.img with Magisk
✅ Phase 4 Complete: Patched /tmp/magisk/magisk_patched.img
⚡ Phase 5: Flashing patched boot.img
✅ Phase 5 Complete: Boot image flashed
🔍 Phase 6: Verifying Magisk installation
✅ Phase 6 Complete: Magisk installation verified
🔧 Phase 7: Enabling Zygisk
✅ Phase 7 Complete: Zygisk enabled
======================================================================
✅ Magisk Installation Complete!
   Version: 30.6
   Duration: 245.3s
   Phases: 7/7 completed
======================================================================
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, MagicMock
from adb_magisk_orchestrator import MagiskOrchestrator

def test_phase1_download():
    device = Mock()
    ui_navigator = Mock()
    orchestrator = MagiskOrchestrator(device, ui_navigator)

    result = orchestrator._phase1_download("latest")
    assert result.success
    assert orchestrator.apk_path is not None
```

### Integration Testing

```python
# Test complete workflow with real device
def test_complete_installation():
    device = AdbDeviceWrapper.create_from_settings()
    ocr_finder = OCRTextFinder(device)
    ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

    orchestrator = MagiskOrchestrator(device, ui_navigator, ocr_finder=ocr_finder)
    result = orchestrator.execute_installation()

    assert result.success
    assert len(result.phases) == 7
    assert result.all_phases_success()
```

## Performance

Typical installation times:

| Phase | Duration | Notes |
|-------|----------|-------|
| Phase 1 | 10-30s | Network dependent |
| Phase 2 | 5-15s | Device speed dependent |
| Phase 3 | 5-10s | Partition size dependent |
| Phase 4 | 30-60s | Processing intensive |
| Phase 5 | 20-40s | Includes reboot |
| Phase 6 | 3-5s | OCR detection |
| Phase 7 | 5-10s | UI navigation |
| **Total** | **78-170s** | ~1.3-2.8 minutes |

## Troubleshooting

### Installation Hangs at Phase 4

**Symptom**: Patching phase never completes

**Solutions**:
1. Check Magisk app UI is visible
2. Verify screen is unlocked
3. Increase timeout in patch script
4. Check logcat for Magisk errors

### OCR Fails to Detect Text

**Symptom**: Phase 6 verification fails with "text not found"

**Solutions**:
1. Adjust OCR confidence threshold
2. Check screen resolution compatibility
3. Verify Tesseract installation
4. Capture screenshot for debugging

### Fastboot Connection Lost

**Symptom**: Phase 5 flash fails with connection error

**Solutions**:
1. Check fastboot drivers installed
2. Verify bootloader unlocked
3. Test fastboot manually: `fastboot devices`
4. Check USB connection stability

## Best Practices

1. **Test on Development Device**: Test full workflow on non-production device first
2. **Backup Boot Image**: Keep backup of original boot.img
3. **Monitor Logs**: Watch logs for early warning signs
4. **Verify Preconditions**: Check bootloader unlocked, storage space, root access
5. **Handle Interruptions**: Implement cleanup on Ctrl+C or process kill

## Security Considerations

1. **Root Access**: Installation grants root access - use responsibly
2. **Bootloader Unlock**: Required for installation, voids warranty
3. **Boot Image Backup**: Critical for recovery if installation fails
4. **Network Security**: Downloads from GitHub over HTTPS
5. **Device Security**: Consider implications of root access

## License

Part of AdbAutoPlayer project. See project LICENSE for details.

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review troubleshooting section
3. Open issue on project repository
4. Include full log output and device info

## Version

**Version**: 1.0.0
**Author**: MoAI-ADK
**Last Updated**: 2025-12-02
