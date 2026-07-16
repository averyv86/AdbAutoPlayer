"""Unit tests for Magisk Installation Orchestrator.

Tests all 7 phases of the Magisk installation workflow with mocked dependencies.

Author: MoAI-ADK
Version: 1.0.0
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from adb_magisk_orchestrator import (
    MagiskOrchestrator,
    PhaseStatus,
    PhaseResult,
    InstallationResult,
    StateVerifier
)


# ========== SECTION 1: FIXTURES ==========

@pytest.fixture
def mock_device():
    """Create mock ADB device."""
    device = Mock()
    device.serial = "127.0.0.1:5555"
    device.shell = Mock(return_value="")
    return device


@pytest.fixture
def mock_ui_navigator():
    """Create mock UI navigator."""
    navigator = Mock()
    navigator.find_and_tap = Mock(return_value=True)
    navigator.navigate_to_button = Mock(return_value=True)
    navigator.handle_dialog = Mock(return_value=True)
    return navigator


@pytest.fixture
def mock_ocr_finder():
    """Create mock OCR finder."""
    finder = Mock()
    finder.find_text = Mock(return_value=Mock(text="Installed", confidence=Mock(value=0.95)))
    finder.wait_for_text = Mock(return_value=True)
    return finder


@pytest.fixture
def mock_state_verifier():
    """Create mock state verifier."""
    verifier = Mock(spec=StateVerifier)
    verifier.check_app_installed = Mock(return_value=True)
    verifier.check_file_exists = Mock(return_value=True)
    verifier.detect_state_change = Mock(return_value=True)
    return verifier


@pytest.fixture
def orchestrator(mock_device, mock_ui_navigator, mock_ocr_finder, mock_state_verifier, tmp_path):
    """Create orchestrator with mocked dependencies."""
    return MagiskOrchestrator(
        device=mock_device,
        ui_navigator=mock_ui_navigator,
        state_verifier=mock_state_verifier,
        ocr_finder=mock_ocr_finder,
        work_dir=str(tmp_path / "magisk")
    )


# ========== SECTION 2: PHASE 1 TESTS (DOWNLOAD) ==========

class TestPhase1Download:
    """Tests for Phase 1: Download Magisk APK."""

    @patch("subprocess.run")
    def test_download_latest_success(self, mock_run, orchestrator, tmp_path):
        """Test successful download of latest version."""
        # Setup mock
        apk_path = tmp_path / "magisk/Magisk-v30.6.apk"
        apk_path.parent.mkdir(parents=True, exist_ok=True)
        apk_path.write_text("mock apk content")

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "version": "30.6", "files": [{"filename": "Magisk-v30.6.apk", "local_path": "' + str(apk_path) + '", "downloaded": true, "size_bytes": 12345}]}'
        )

        # Execute
        result = orchestrator._phase1_download("latest")

        # Verify
        assert result.success
        assert result.status == PhaseStatus.SUCCESS
        assert orchestrator.magisk_version == "30.6"
        assert orchestrator.apk_path == apk_path
        assert result.data["size_bytes"] == 12345

    @patch("subprocess.run")
    def test_download_specific_version(self, mock_run, orchestrator, tmp_path):
        """Test download of specific version."""
        apk_path = tmp_path / "magisk/Magisk-v27.0.apk"
        apk_path.parent.mkdir(parents=True, exist_ok=True)
        apk_path.write_text("mock apk")

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "version": "27.0", "files": [{"filename": "Magisk-v27.0.apk", "local_path": "' + str(apk_path) + '", "downloaded": true, "size_bytes": 10000}]}'
        )

        result = orchestrator._phase1_download("27.0")

        assert result.success
        assert orchestrator.magisk_version == "27.0"

    @patch("subprocess.run")
    def test_download_failure(self, mock_run, orchestrator):
        """Test download failure."""
        mock_run.return_value = Mock(
            returncode=2,
            stderr="Network error",
            stdout='{"success": false, "error": "Network error"}'
        )

        result = orchestrator._phase1_download("latest")

        assert not result.success
        assert result.status == PhaseStatus.FAILED
        assert "Network error" in result.error

    @patch("subprocess.run")
    def test_download_script_not_found(self, mock_run, orchestrator):
        """Test error when download script not found."""
        with patch.object(Path, "exists", return_value=False):
            result = orchestrator._phase1_download("latest")

            assert not result.success
            assert "not found" in result.error.lower()


# ========== SECTION 3: PHASE 2 TESTS (INSTALL) ==========

class TestPhase2Install:
    """Tests for Phase 2: Install Magisk APK."""

    @patch("subprocess.run")
    def test_install_success(self, mock_run, orchestrator, tmp_path):
        """Test successful APK installation."""
        # Setup
        orchestrator.apk_path = tmp_path / "Magisk-v30.6.apk"
        orchestrator.apk_path.write_text("mock apk")

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "app_installed": true, "verification_passed": true}'
        )

        # Execute
        result = orchestrator._phase2_install()

        # Verify
        assert result.success
        assert result.status == PhaseStatus.SUCCESS
        assert result.data["app_installed"]
        assert result.data["verification_passed"]

    def test_install_apk_not_found(self, orchestrator):
        """Test error when APK not found."""
        orchestrator.apk_path = Path("/nonexistent/magisk.apk")

        result = orchestrator._phase2_install()

        assert not result.success
        assert "not found" in result.error.lower()

    @patch("subprocess.run")
    def test_install_verification_failed(self, mock_run, orchestrator, tmp_path, mock_state_verifier):
        """Test installation but verification failed."""
        orchestrator.apk_path = tmp_path / "Magisk.apk"
        orchestrator.apk_path.write_text("mock")
        orchestrator.state_verifier.check_app_installed = Mock(return_value=False)

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "app_installed": true, "verification_passed": false}'
        )

        result = orchestrator._phase2_install()

        assert not result.success
        assert "not detected" in result.error.lower()


# ========== SECTION 4: PHASE 3 TESTS (EXTRACT) ==========

class TestPhase3Extract:
    """Tests for Phase 3: Extract boot.img."""

    @patch("subprocess.run")
    def test_extract_success(self, mock_run, orchestrator, tmp_path):
        """Test successful boot image extraction."""
        boot_path = tmp_path / "magisk/boot.img"
        boot_path.parent.mkdir(parents=True, exist_ok=True)
        boot_path.write_bytes(b"mock boot image" * 1000)

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "boot_path": "' + str(boot_path) + '", "size_bytes": 15000}'
        )

        result = orchestrator._phase3_extract_boot()

        assert result.success
        assert orchestrator.boot_img_path == boot_path
        assert result.data["size_bytes"] > 0

    @patch("subprocess.run")
    def test_extract_script_not_found(self, mock_run, orchestrator):
        """Test error when extract script not found."""
        with patch.object(Path, "exists", return_value=False):
            result = orchestrator._phase3_extract_boot()

            assert not result.success
            assert "not found" in result.error.lower()

    @patch("subprocess.run")
    def test_extract_failure(self, mock_run, orchestrator):
        """Test extraction failure."""
        mock_run.return_value = Mock(
            returncode=2,
            stderr="Device not rooted",
            stdout='{"success": false, "error": "Device not rooted"}'
        )

        result = orchestrator._phase3_extract_boot()

        assert not result.success
        assert "not rooted" in result.error.lower()


# ========== SECTION 5: PHASE 4 TESTS (PATCH) ==========

class TestPhase4Patch:
    """Tests for Phase 4: Patch boot.img."""

    @patch("subprocess.run")
    def test_patch_success(self, mock_run, orchestrator, tmp_path):
        """Test successful boot image patching."""
        orchestrator.boot_img_path = tmp_path / "boot.img"
        orchestrator.boot_img_path.write_bytes(b"boot")

        patched_path = tmp_path / "magisk_patched.img"
        patched_path.write_bytes(b"patched boot")

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "patched_boot_path": "' + str(patched_path) + '"}'
        )

        result = orchestrator._phase4_patch_boot()

        assert result.success
        assert orchestrator.patched_boot_path == patched_path

    def test_patch_boot_not_found(self, orchestrator):
        """Test error when boot image not found."""
        orchestrator.boot_img_path = Path("/nonexistent/boot.img")

        result = orchestrator._phase4_patch_boot()

        assert not result.success
        assert "not found" in result.error.lower()

    @patch("subprocess.run")
    def test_patch_timeout(self, mock_run, orchestrator, tmp_path):
        """Test patch timeout."""
        orchestrator.boot_img_path = tmp_path / "boot.img"
        orchestrator.boot_img_path.write_bytes(b"boot")

        mock_run.side_effect = subprocess.TimeoutExpired("patch", 180)

        result = orchestrator._phase4_patch_boot()

        assert not result.success


# ========== SECTION 6: PHASE 5 TESTS (FLASH) ==========

class TestPhase5Flash:
    """Tests for Phase 5: Flash boot.img."""

    @patch("subprocess.run")
    def test_flash_success(self, mock_run, orchestrator, tmp_path):
        """Test successful boot image flashing."""
        orchestrator.patched_boot_path = tmp_path / "magisk_patched.img"
        orchestrator.patched_boot_path.write_bytes(b"patched")

        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"success": true, "boot_flashed": true}'
        )

        result = orchestrator._phase5_flash_boot()

        assert result.success
        assert result.data["boot_flashed"]

    def test_flash_patched_not_found(self, orchestrator):
        """Test error when patched boot not found."""
        orchestrator.patched_boot_path = Path("/nonexistent/patched.img")

        result = orchestrator._phase5_flash_boot()

        assert not result.success

    @patch("subprocess.run")
    def test_flash_fastboot_failure(self, mock_run, orchestrator, tmp_path):
        """Test fastboot failure."""
        orchestrator.patched_boot_path = tmp_path / "patched.img"
        orchestrator.patched_boot_path.write_bytes(b"patched")

        mock_run.return_value = Mock(
            returncode=1,
            stderr="Fastboot not found",
            stdout='{"success": false, "error": "Fastboot not found"}'
        )

        result = orchestrator._phase5_flash_boot()

        assert not result.success


# ========== SECTION 7: PHASE 6 TESTS (VERIFY) ==========

class TestPhase6Verify:
    """Tests for Phase 6: Verify installation."""

    def test_verify_success_with_ocr(self, orchestrator, mock_ocr_finder):
        """Test successful verification with OCR."""
        orchestrator.magisk_version = "30.6"

        result = orchestrator._phase6_verify_installation()

        assert result.success
        assert result.data["installed"]
        assert result.data["verified"]
        mock_ocr_finder.wait_for_text.assert_called_with("Installed", timeout_seconds=10)

    def test_verify_ocr_text_not_found(self, orchestrator, mock_ocr_finder):
        """Test verification failure when OCR text not found."""
        mock_ocr_finder.wait_for_text = Mock(return_value=False)

        result = orchestrator._phase6_verify_installation()

        assert not result.success
        assert "not found" in result.error.lower()

    def test_verify_without_ocr(self, orchestrator, mock_state_verifier):
        """Test verification without OCR (fallback)."""
        orchestrator.ocr_finder = None

        result = orchestrator._phase6_verify_installation()

        assert result.success
        mock_state_verifier.check_app_installed.assert_called()


# ========== SECTION 8: PHASE 7 TESTS (ZYGISK) ==========

class TestPhase7Zygisk:
    """Tests for Phase 7: Enable Zygisk."""

    @patch("subprocess.run")
    def test_zygisk_enable_success(self, mock_run, orchestrator):
        """Test successful Zygisk enablement."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"zygisk_enabled": true, "reboot_requested": false}'
        )

        result = orchestrator._phase7_enable_zygisk()

        assert result.success
        assert result.data["zygisk_enabled"]

    @patch("subprocess.run")
    def test_zygisk_enable_with_reboot(self, mock_run, orchestrator):
        """Test Zygisk enablement requiring reboot."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='{"zygisk_enabled": true, "reboot_requested": true}'
        )

        result = orchestrator._phase7_enable_zygisk()

        assert result.success
        assert result.data["reboot_required"]

    @patch("subprocess.run")
    def test_zygisk_script_not_found(self, mock_run, orchestrator):
        """Test error when enable script not found."""
        with patch.object(Path, "exists", return_value=False):
            result = orchestrator._phase7_enable_zygisk()

            assert not result.success


# ========== SECTION 9: ORCHESTRATION TESTS ==========

class TestOrchestration:
    """Tests for complete workflow orchestration."""

    @patch.object(MagiskOrchestrator, "_phase1_download")
    @patch.object(MagiskOrchestrator, "_phase2_install")
    @patch.object(MagiskOrchestrator, "_phase3_extract_boot")
    @patch.object(MagiskOrchestrator, "_phase4_patch_boot")
    @patch.object(MagiskOrchestrator, "_phase5_flash_boot")
    @patch.object(MagiskOrchestrator, "_phase6_verify_installation")
    @patch.object(MagiskOrchestrator, "_phase7_enable_zygisk")
    def test_complete_installation_success(
        self, mock_p7, mock_p6, mock_p5, mock_p4, mock_p3, mock_p2, mock_p1, orchestrator
    ):
        """Test complete installation workflow success."""
        # Setup all phases to succeed
        for i, mock_phase in enumerate([mock_p1, mock_p2, mock_p3, mock_p4, mock_p5, mock_p6, mock_p7], 1):
            mock_phase.return_value = PhaseResult(
                phase_number=i,
                phase_name=f"Phase {i}",
                status=PhaseStatus.SUCCESS
            )

        # Execute
        result = orchestrator.execute_installation()

        # Verify
        assert result.success
        assert len(result.phases) == 7
        assert result.all_phases_success()

    @patch.object(MagiskOrchestrator, "_phase1_download")
    @patch.object(MagiskOrchestrator, "_phase2_install")
    def test_installation_fails_at_phase2(self, mock_p2, mock_p1, orchestrator):
        """Test installation stops when phase fails."""
        # Phase 1 succeeds
        mock_p1.return_value = PhaseResult(
            phase_number=1,
            phase_name="Download",
            status=PhaseStatus.SUCCESS
        )

        # Phase 2 fails
        mock_p2.return_value = PhaseResult(
            phase_number=2,
            phase_name="Install",
            status=PhaseStatus.FAILED,
            error="Installation failed"
        )

        # Execute
        result = orchestrator.execute_installation()

        # Verify
        assert not result.success
        assert len(result.phases) == 2
        assert "Phase 2 failed" in result.error

    def test_skip_phases(self, orchestrator):
        """Test skipping specific phases."""
        with patch.object(MagiskOrchestrator, "_phase1_download") as mock_p1:
            with patch.object(MagiskOrchestrator, "_phase2_install") as mock_p2:
                mock_p2.return_value = PhaseResult(
                    phase_number=2,
                    phase_name="Install",
                    status=PhaseStatus.FAILED
                )

                result = orchestrator.execute_installation(skip_phases=[1])

                # Phase 1 should not be called
                mock_p1.assert_not_called()


# ========== SECTION 10: RETRY LOGIC TESTS ==========

class TestRetryLogic:
    """Tests for retry logic."""

    def test_retry_on_failure(self, orchestrator):
        """Test phase retries on failure."""
        mock_func = Mock(side_effect=[
            PhaseResult(phase_number=1, phase_name="Test", status=PhaseStatus.FAILED, error="Error 1"),
            PhaseResult(phase_number=1, phase_name="Test", status=PhaseStatus.FAILED, error="Error 2"),
            PhaseResult(phase_number=1, phase_name="Test", status=PhaseStatus.SUCCESS)
        ])

        result = orchestrator._execute_phase_with_retry(mock_func, [], max_retries=3)

        assert result.success
        assert result.retry_count == 2
        assert mock_func.call_count == 3

    def test_retry_exhausted(self, orchestrator):
        """Test all retries exhausted."""
        mock_func = Mock(return_value=PhaseResult(
            phase_number=1,
            phase_name="Test",
            status=PhaseStatus.FAILED,
            error="Persistent error"
        ))

        result = orchestrator._execute_phase_with_retry(mock_func, [], max_retries=3)

        assert not result.success
        assert "Failed after 3 attempts" in result.error
        assert mock_func.call_count == 3


# ========== SECTION 11: HELPER TESTS ==========

class TestHelpers:
    """Tests for helper methods."""

    def test_find_project_root(self, orchestrator, tmp_path):
        """Test finding project root."""
        # Create mock project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()

        with patch("pathlib.Path.cwd", return_value=project_dir / "subdir"):
            root = orchestrator._find_project_root()

            # Should find .git directory
            assert (root / ".git").exists()

    def test_launch_magisk_app(self, orchestrator, mock_device):
        """Test launching Magisk app."""
        result = orchestrator._launch_magisk_app()

        assert result
        mock_device.shell.assert_called()


# ========== SECTION 12: STATE VERIFIER TESTS ==========

class TestStateVerifier:
    """Tests for StateVerifier class."""

    def test_check_app_installed(self, mock_device):
        """Test checking if app is installed."""
        verifier = StateVerifier(mock_device)
        mock_device.shell.return_value = "package:com.topjohnwu.magisk"

        result = verifier.check_app_installed("com.topjohnwu.magisk")

        assert result

    def test_check_file_exists(self, mock_device):
        """Test checking if file exists."""
        verifier = StateVerifier(mock_device)
        mock_device.shell.return_value = "/data/boot.img"

        result = verifier.check_file_exists("/data/boot.img")

        assert result

    def test_check_file_not_exists(self, mock_device):
        """Test checking file that doesn't exist."""
        verifier = StateVerifier(mock_device)
        mock_device.shell.return_value = "No such file or directory"

        result = verifier.check_file_exists("/nonexistent/file")

        assert not result


# ========== SECTION 13: INTEGRATION TESTS ==========

class TestIntegration:
    """Integration tests with real-like scenarios."""

    @pytest.mark.integration
    def test_complete_workflow_realistic(self, orchestrator, tmp_path):
        """Test complete workflow with realistic timing."""
        # This test would require actual device/scripts
        # Skipped in unit tests, run separately in integration suite
        pytest.skip("Integration test - requires real device")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=adb_magisk_orchestrator"])
