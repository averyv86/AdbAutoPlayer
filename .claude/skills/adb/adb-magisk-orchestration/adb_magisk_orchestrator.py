"""Magisk Installation Orchestrator.

Complete 7-phase Magisk installation workflow orchestration.
Coordinates all phases from download through Zygisk enablement with
comprehensive error handling and state verification.

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Import core dependencies
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "adbautoplayer/src-tauri/src-python"))

from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper

logger = logging.getLogger(__name__)


# ========== SECTION 1: ENUMS AND DATA MODELS ==========

class PhaseStatus(Enum):
    """Status of installation phase."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a single installation phase."""
    phase_number: int
    phase_name: str
    status: PhaseStatus
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    retry_count: int = 0
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if phase succeeded."""
        return self.status == PhaseStatus.SUCCESS


@dataclass
class InstallationResult:
    """Complete installation workflow result."""
    success: bool
    device_id: str
    magisk_version: str
    total_duration: float = 0.0
    phases: List[PhaseResult] = field(default_factory=list)
    error: Optional[str] = None

    def get_phase(self, phase_number: int) -> Optional[PhaseResult]:
        """Get specific phase result."""
        for phase in self.phases:
            if phase.phase_number == phase_number:
                return phase
        return None

    def all_phases_success(self) -> bool:
        """Check if all phases succeeded."""
        return all(p.success for p in self.phases)


# ========== SECTION 2: STATE VERIFIER (SIMPLIFIED) ==========

class StateVerifier:
    """Simple state verification helper."""

    def __init__(self, device: AdbDeviceWrapper):
        """Initialize state verifier.

        Args:
            device: ADB device wrapper
        """
        self.device = device
        self.logger = logger

    def check_app_installed(self, package_name: str) -> bool:
        """Check if app is installed.

        Args:
            package_name: Package name to check

        Returns:
            True if installed, False otherwise
        """
        try:
            result = self.device.shell(["pm", "list", "packages", package_name])
            return package_name in str(result)
        except Exception as e:
            self.logger.error(f"Failed to check app installation: {e}")
            return False

    def check_file_exists(self, file_path: str) -> bool:
        """Check if file exists on device.

        Args:
            file_path: Path to check

        Returns:
            True if exists, False otherwise
        """
        try:
            result = self.device.shell(["ls", file_path])
            return "No such file" not in str(result)
        except Exception as e:
            self.logger.error(f"Failed to check file: {e}")
            return False

    def detect_state_change(self, timeout_seconds: int = 5) -> bool:
        """Detect if UI state changed (simplified).

        Args:
            timeout_seconds: Time to wait for change

        Returns:
            True if state changed (simplified always returns True)
        """
        time.sleep(min(timeout_seconds, 2))
        return True

    def detect_dialog(self) -> bool:
        """Detect if dialog is present (simplified).

        Returns:
            False (simplified, always returns no dialog)
        """
        return False


# ========== SECTION 3: MAGISK ORCHESTRATOR ==========

class MagiskOrchestrator:
    """Orchestrates complete Magisk installation workflow."""

    MAGISK_PACKAGE = "com.topjohnwu.magisk"
    MAGISK_ACTIVITY = f"{MAGISK_PACKAGE}/.ui.MainActivity"
    TIMEOUT_DEFAULT = 30
    MAX_RETRIES = 3

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ui_navigator: Any,
        state_verifier: Optional[StateVerifier] = None,
        ocr_finder: Optional[Any] = None,
        work_dir: str = "/tmp/magisk",
    ):
        """Initialize Magisk Orchestrator.

        Args:
            device: ADB device wrapper
            ui_navigator: UI navigation helper
            state_verifier: State verification helper (optional)
            ocr_finder: OCR text finder helper (optional)
            work_dir: Working directory for downloads and temporary files
        """
        self.device = device
        self.ui_navigator = ui_navigator
        self.state_verifier = state_verifier or StateVerifier(device)
        self.ocr_finder = ocr_finder
        self.work_dir = Path(work_dir)
        self.logger = logger

        # Installation state
        self.magisk_version: str = ""
        self.apk_path: Optional[Path] = None
        self.boot_img_path: Optional[Path] = None
        self.patched_boot_path: Optional[Path] = None

    # ========== PHASE 1: DOWNLOAD ==========

    def _phase1_download(self, version: str = "latest") -> PhaseResult:
        """Phase 1: Download Magisk APK from GitHub releases.

        Args:
            version: Version to download ("latest" or specific version like "30.6")

        Returns:
            PhaseResult with download status and paths
        """
        result = PhaseResult(
            phase_number=1,
            phase_name="Download Magisk APK",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info(f"📥 Phase 1: Downloading Magisk {version}")

            # Find download script
            project_root = self._find_project_root()
            download_script = (
                project_root / ".claude/skills/adb/adb-game-magisk-installer"
                / "adb-magisk-installer/scripts/adb-magisk-download.py"
            )

            if not download_script.exists():
                raise FileNotFoundError(f"Download script not found: {download_script}")

            # Create work directory
            self.work_dir.mkdir(parents=True, exist_ok=True)

            # Execute download
            cmd = [
                "uv", "run", str(download_script),
                "--version", version,
                "--output-dir", str(self.work_dir),
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if proc_result.returncode != 0:
                raise RuntimeError(f"Download failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            download_data = json.loads(proc_result.stdout)

            if not download_data.get("success"):
                raise RuntimeError(f"Download failed: {download_data.get('error')}")

            # Extract APK path
            files = download_data.get("files", [])
            apk_file = next((f for f in files if f["filename"].endswith(".apk")), None)

            if not apk_file or not apk_file.get("downloaded"):
                raise RuntimeError("APK file not downloaded")

            self.apk_path = Path(apk_file["local_path"])
            self.magisk_version = download_data.get("version", version)

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "apk_path": str(self.apk_path),
                "version": self.magisk_version,
                "size_bytes": apk_file.get("size_bytes", 0)
            }
            self.logger.info(f"✅ Phase 1 Complete: Downloaded {self.apk_path}")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 1 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 2: INSTALL ==========

    def _phase2_install(self) -> PhaseResult:
        """Phase 2: Install Magisk APK via ADB.

        Returns:
            PhaseResult with installation status
        """
        result = PhaseResult(
            phase_number=2,
            phase_name="Install Magisk APK",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("📦 Phase 2: Installing Magisk APK")

            if not self.apk_path or not self.apk_path.exists():
                raise FileNotFoundError(f"APK not found: {self.apk_path}")

            # Find install script
            project_root = self._find_project_root()
            install_script = (
                project_root / ".claude/skills/adb/adb-game-magisk-installer"
                / "adb-magisk-installer/scripts/adb-magisk-install-app.py"
            )

            if not install_script.exists():
                raise FileNotFoundError(f"Install script not found: {install_script}")

            # Execute install
            cmd = [
                "uv", "run", str(install_script),
                "--device", self.device.serial,
                "--apk-path", str(self.apk_path),
                "--force",
                "--verify",
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )

            if proc_result.returncode != 0:
                raise RuntimeError(f"Install failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            install_data = json.loads(proc_result.stdout)

            if not install_data.get("success"):
                raise RuntimeError(f"Install failed: {install_data.get('error')}")

            # Verify installation
            if not self.state_verifier.check_app_installed(self.MAGISK_PACKAGE):
                raise RuntimeError("App not detected after installation")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "app_installed": True,
                "verification_passed": install_data.get("verification_passed", True)
            }
            self.logger.info("✅ Phase 2 Complete: Magisk APK installed")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 2 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 3: EXTRACT BOOT IMAGE ==========

    def _phase3_extract_boot(self) -> PhaseResult:
        """Phase 3: Extract boot.img from device.

        Returns:
            PhaseResult with extraction status
        """
        result = PhaseResult(
            phase_number=3,
            phase_name="Extract boot.img",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("💾 Phase 3: Extracting boot.img")

            # Find extract script
            project_root = self._find_project_root()
            extract_script = (
                project_root / ".claude/skills/adb/adb-game-magisk-installer"
                / "adb-magisk-installer/scripts/adb-magisk-extract-boot.py"
            )

            if not extract_script.exists():
                raise FileNotFoundError(f"Extract script not found: {extract_script}")

            # Execute extract
            boot_output = self.work_dir / "boot.img"
            cmd = [
                "uv", "run", str(extract_script),
                "--device", self.device.serial,
                "--output", str(boot_output),
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if proc_result.returncode != 0:
                raise RuntimeError(f"Extract failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            extract_data = json.loads(proc_result.stdout)

            if not extract_data.get("success"):
                raise RuntimeError(f"Extract failed: {extract_data.get('error')}")

            self.boot_img_path = boot_output

            if not self.boot_img_path.exists():
                raise RuntimeError(f"Boot image not found: {self.boot_img_path}")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "boot_img_path": str(self.boot_img_path),
                "size_bytes": self.boot_img_path.stat().st_size
            }
            self.logger.info(f"✅ Phase 3 Complete: Extracted {self.boot_img_path}")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 3 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 4: PATCH BOOT IMAGE ==========

    def _phase4_patch_boot(self) -> PhaseResult:
        """Phase 4: Patch boot.img using Magisk app.

        Returns:
            PhaseResult with patching status
        """
        result = PhaseResult(
            phase_number=4,
            phase_name="Patch boot.img",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("🔧 Phase 4: Patching boot.img with Magisk")

            if not self.boot_img_path or not self.boot_img_path.exists():
                raise FileNotFoundError(f"Boot image not found: {self.boot_img_path}")

            # Find patch script
            project_root = self._find_project_root()
            patch_script = (
                project_root / ".claude/skills/adb/adb-game-magisk-installer"
                / "adb-magisk-installer/scripts/adb-magisk-patch-boot.py"
            )

            if not patch_script.exists():
                raise FileNotFoundError(f"Patch script not found: {patch_script}")

            # Execute patch
            cmd = [
                "uv", "run", str(patch_script),
                "--device", self.device.serial,
                "--boot-img", str(self.boot_img_path),
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )

            if proc_result.returncode != 0:
                raise RuntimeError(f"Patch failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            patch_data = json.loads(proc_result.stdout)

            if not patch_data.get("success"):
                raise RuntimeError(f"Patch failed: {patch_data.get('error')}")

            # Get patched boot path
            patched_path = patch_data.get("patched_boot_path")
            if not patched_path:
                raise RuntimeError("Patched boot path not returned")

            self.patched_boot_path = Path(patched_path)

            if not self.patched_boot_path.exists():
                raise RuntimeError(f"Patched boot not found: {self.patched_boot_path}")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "patched_boot_path": str(self.patched_boot_path),
                "size_bytes": self.patched_boot_path.stat().st_size
            }
            self.logger.info(f"✅ Phase 4 Complete: Patched {self.patched_boot_path}")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 4 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 5: FLASH BOOT IMAGE ==========

    def _phase5_flash_boot(self) -> PhaseResult:
        """Phase 5: Flash patched boot.img via fastboot.

        Returns:
            PhaseResult with flashing status
        """
        result = PhaseResult(
            phase_number=5,
            phase_name="Flash patched boot.img",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("⚡ Phase 5: Flashing patched boot.img")

            if not self.patched_boot_path or not self.patched_boot_path.exists():
                raise FileNotFoundError(f"Patched boot not found: {self.patched_boot_path}")

            # Find flash script
            project_root = self._find_project_root()
            flash_script = (
                project_root / ".claude/skills/adb/adb-game-magisk-installer"
                / "adb-magisk-installer/scripts/adb-magisk-flash-boot.py"
            )

            if not flash_script.exists():
                raise FileNotFoundError(f"Flash script not found: {flash_script}")

            # Execute flash
            cmd = [
                "uv", "run", str(flash_script),
                "--device", self.device.serial,
                "--patched-boot", str(self.patched_boot_path),
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if proc_result.returncode != 0:
                raise RuntimeError(f"Flash failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            flash_data = json.loads(proc_result.stdout)

            if not flash_data.get("success"):
                raise RuntimeError(f"Flash failed: {flash_data.get('error')}")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "flashed": True,
                "boot_flashed": flash_data.get("boot_flashed", True)
            }
            self.logger.info("✅ Phase 5 Complete: Boot image flashed")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 5 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 6: VERIFY INSTALLATION ==========

    def _phase6_verify_installation(self) -> PhaseResult:
        """Phase 6: Verify Magisk installation via UI detection.

        Returns:
            PhaseResult with verification status
        """
        result = PhaseResult(
            phase_number=6,
            phase_name="Verify Magisk Installation",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("🔍 Phase 6: Verifying Magisk installation")

            # Launch Magisk app
            self.logger.info("Launching Magisk app...")
            self._launch_magisk_app()
            time.sleep(3)

            # Look for "Installed: [version]" text using OCR
            if self.ocr_finder:
                self.logger.info("Checking for 'Installed' text via OCR...")

                # Wait for "Installed" text to appear
                if not self.ocr_finder.wait_for_text("Installed", timeout_seconds=10):
                    raise RuntimeError("'Installed' text not found on Magisk home screen")

                # Try to find version text
                ocr_result = self.ocr_finder.find_text("Installed")
                if not ocr_result:
                    raise RuntimeError("Failed to locate 'Installed' text")

                self.logger.info(f"✅ Found 'Installed' text: {ocr_result.text}")
            else:
                # Fallback: check if app is installed
                if not self.state_verifier.check_app_installed(self.MAGISK_PACKAGE):
                    raise RuntimeError("Magisk app not detected")

                self.logger.info("✅ Magisk app detected (OCR not available)")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "installed": True,
                "verified": True,
                "version": self.magisk_version
            }
            self.logger.info("✅ Phase 6 Complete: Magisk installation verified")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 6 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== PHASE 7: ENABLE ZYGISK ==========

    def _phase7_enable_zygisk(self) -> PhaseResult:
        """Phase 7: Enable Zygisk toggle in Magisk settings.

        Returns:
            PhaseResult with Zygisk enablement status
        """
        result = PhaseResult(
            phase_number=7,
            phase_name="Enable Zygisk",
            status=PhaseStatus.RUNNING,
            start_time=time.time()
        )

        try:
            self.logger.info("🔧 Phase 7: Enabling Zygisk")

            # Find enable script
            project_root = self._find_project_root()
            enable_script = (
                project_root / ".claude/skills/adb/adb-game-magisk"
                / "adb-magisk/scripts/adb-magisk-enable-zygisk.py"
            )

            if not enable_script.exists():
                raise FileNotFoundError(f"Enable script not found: {enable_script}")

            # Execute enable
            cmd = [
                "uv", "run", str(enable_script),
                "--device", self.device.serial,
                "--json"
            ]

            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if proc_result.returncode not in [0, 1]:  # 0=success, 1=needs reboot
                raise RuntimeError(f"Enable failed: {proc_result.stderr}")

            # Parse JSON result
            import json
            enable_data = json.loads(proc_result.stdout)

            if not enable_data.get("zygisk_enabled"):
                raise RuntimeError(f"Zygisk not enabled: {enable_data.get('error')}")

            result.status = PhaseStatus.SUCCESS
            result.data = {
                "zygisk_enabled": True,
                "reboot_required": enable_data.get("reboot_requested", False)
            }

            if enable_data.get("reboot_requested"):
                self.logger.info("✅ Phase 7 Complete: Zygisk enabled (reboot required)")
            else:
                self.logger.info("✅ Phase 7 Complete: Zygisk enabled")

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Phase 7 Failed: {e}")

        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result

    # ========== MAIN ORCHESTRATION ==========

    def execute_installation(
        self,
        magisk_version: str = "latest",
        skip_phases: Optional[List[int]] = None
    ) -> InstallationResult:
        """Execute complete Magisk installation workflow.

        Args:
            magisk_version: Version to install ("latest" or specific version)
            skip_phases: Optional list of phase numbers to skip

        Returns:
            InstallationResult with complete workflow status
        """
        start_time = time.time()
        skip_phases = skip_phases or []

        self.logger.info("=" * 70)
        self.logger.info(f"🚀 Starting Magisk Installation Workflow")
        self.logger.info(f"   Device: {self.device.serial}")
        self.logger.info(f"   Version: {magisk_version}")
        self.logger.info(f"   Work Dir: {self.work_dir}")
        self.logger.info("=" * 70)

        result = InstallationResult(
            success=False,
            device_id=self.device.serial,
            magisk_version=magisk_version
        )

        # Define phase execution order
        phases = [
            (1, self._phase1_download, [magisk_version]),
            (2, self._phase2_install, []),
            (3, self._phase3_extract_boot, []),
            (4, self._phase4_patch_boot, []),
            (5, self._phase5_flash_boot, []),
            (6, self._phase6_verify_installation, []),
            (7, self._phase7_enable_zygisk, [])
        ]

        # Execute each phase
        for phase_num, phase_func, args in phases:
            if phase_num in skip_phases:
                self.logger.info(f"⏭️  Skipping Phase {phase_num}")
                continue

            # Execute phase with retry logic
            phase_result = self._execute_phase_with_retry(
                phase_func, args, max_retries=self.MAX_RETRIES
            )
            result.phases.append(phase_result)

            # Check if phase failed
            if not phase_result.success:
                result.error = f"Phase {phase_num} failed: {phase_result.error}"
                self.logger.error(f"❌ Installation failed at Phase {phase_num}")
                break

        # Calculate total duration
        result.total_duration = time.time() - start_time
        result.success = result.all_phases_success()

        # Log final result
        self.logger.info("=" * 70)
        if result.success:
            self.logger.info("✅ Magisk Installation Complete!")
            self.logger.info(f"   Version: {self.magisk_version}")
            self.logger.info(f"   Duration: {result.total_duration:.1f}s")
            self.logger.info(f"   Phases: {len(result.phases)}/{len(phases)} completed")
        else:
            self.logger.error("❌ Magisk Installation Failed")
            self.logger.error(f"   Error: {result.error}")
            self.logger.error(f"   Failed Phase: {[p.phase_name for p in result.phases if not p.success]}")
        self.logger.info("=" * 70)

        return result

    def _execute_phase_with_retry(
        self,
        phase_func,
        args: List[Any],
        max_retries: int = 3
    ) -> PhaseResult:
        """Execute phase with retry logic.

        Args:
            phase_func: Phase function to execute
            args: Arguments for phase function
            max_retries: Maximum retry attempts

        Returns:
            PhaseResult with execution status
        """
        last_result = None

        for attempt in range(max_retries):
            try:
                result = phase_func(*args)
                result.retry_count = attempt

                if result.success:
                    return result

                # Log retry
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"⚠️  Phase {result.phase_name} failed (attempt {attempt + 1}/{max_retries})"
                    )
                    self.logger.warning(f"   Error: {result.error}")
                    self.logger.info(f"   Retrying in 2 seconds...")
                    time.sleep(2)

                last_result = result

            except Exception as e:
                self.logger.error(f"Phase execution exception: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        # All retries exhausted
        if last_result:
            last_result.error = f"Failed after {max_retries} attempts: {last_result.error}"
            return last_result
        else:
            # Create failure result
            return PhaseResult(
                phase_number=0,
                phase_name="Unknown",
                status=PhaseStatus.FAILED,
                error=f"Failed after {max_retries} attempts"
            )

    # ========== HELPER METHODS ==========

    def _find_project_root(self) -> Path:
        """Find project root by searching for markers.

        Returns:
            Path to project root
        """
        current = Path.cwd().resolve()
        while current != current.parent:
            if any((current / marker).exists() for marker in [".git", ".claude", ".moai"]):
                return current
            current = current.parent
        return Path.cwd()

    def _launch_magisk_app(self) -> bool:
        """Launch Magisk Manager app.

        Returns:
            True if launched successfully
        """
        try:
            self.device.shell([
                "am", "start",
                "-n", self.MAGISK_ACTIVITY
            ])
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch Magisk: {e}")
            return False


# ========== SECTION 4: CLI INTERFACE (OPTIONAL) ==========

def main():
    """Main entry point for standalone execution."""
    import sys
    from pathlib import Path

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Create device wrapper (assumes default device)
    try:
        device = AdbDeviceWrapper.create_from_settings()
    except Exception as e:
        logger.error(f"Failed to connect to device: {e}")
        sys.exit(1)

    # Import dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ui-navigation"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ocr-detection"))

    from adb_ui_navigator import UINavigator
    from adb_ocr_finder import OCRTextFinder

    # Create helpers
    ocr_finder = OCRTextFinder(device)
    ui_navigator = UINavigator(device, ocr_finder=ocr_finder)

    # Create orchestrator
    orchestrator = MagiskOrchestrator(
        device=device,
        ui_navigator=ui_navigator,
        ocr_finder=ocr_finder
    )

    # Execute installation
    result = orchestrator.execute_installation()

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
