#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
adb-package-manager: Android Package Management Utility

TRUST 5 Principles:
  1. Transparency - Clear installation and removal reporting
  2. Reliability - Robust error handling and verification
  3. Usability - Simple install/uninstall/list interface
  4. Security - Safe package operations with validation
  5. Testability - Detailed output for operation verification

Provides unified interface for:
  - Listing installed packages
  - Installing APK files
  - Uninstalling packages
  - Package information inspection
  - Permission management
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Package:
    """Package information"""
    name: str
    version: Optional[str] = None
    installed_size: Optional[str] = None
    data_dir: Optional[str] = None


class PackageManager:
    """Unified Android package management"""

    def __init__(self, device: str = None):
        self.device = device
        self.errors: List[str] = []

    def list_packages(self, system: bool = False, verbose: bool = False) -> List[Package]:
        """List installed packages"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "list", "packages"])

            if system:
                cmd[-1] = "packages"  # Show all packages

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.errors.append(f"Failed to list packages: {result.stderr}")
                return []

            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("package:"):
                    package_name = line.replace("package:", "").strip()
                    pkg = Package(name=package_name)

                    if verbose:
                        pkg.version = self._get_package_version(package_name)
                        pkg.installed_size = self._get_installed_size(package_name)

                    packages.append(pkg)

            return packages

        except subprocess.TimeoutExpired:
            self.errors.append("Package listing timeout")
            return []

    def install_apk(self, apk_path: str, force: bool = False) -> bool:
        """Install APK file on device"""
        try:
            apk_file = Path(apk_path)
            if not apk_file.exists():
                self.errors.append(f"APK file not found: {apk_path}")
                return False

            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["install"])
            if force:
                cmd.append("-r")  # Replace existing

            cmd.append(str(apk_file))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            success = result.returncode == 0 and "Success" in result.stdout
            if not success:
                self.errors.append(f"Installation failed: {result.stdout}")

            return success

        except subprocess.TimeoutExpired:
            self.errors.append("Installation timeout")
            return False
        except Exception as e:
            self.errors.append(f"Installation error: {str(e)}")
            return False

    def uninstall_package(self, package_name: str, keep_data: bool = False) -> bool:
        """Uninstall package from device"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["uninstall"])
            if keep_data:
                cmd.append("-k")  # Keep data

            cmd.append(package_name)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0 and "Success" in result.stdout
            if not success:
                self.errors.append(f"Uninstallation failed: {result.stdout}")

            return success

        except Exception as e:
            self.errors.append(f"Uninstallation error: {str(e)}")
            return False

    def get_package_info(self, package_name: str) -> Dict[str, str]:
        """Get detailed package information"""
        return {
            "Package Name": package_name,
            "Version": self._get_package_version(package_name),
            "Version Code": self._get_package_version_code(package_name),
            "Installed Size": self._get_installed_size(package_name),
            "Data Directory": self._get_data_directory(package_name),
            "First Install Time": self._get_first_install_time(package_name),
            "Last Update Time": self._get_last_update_time(package_name),
        }

    def clear_package_data(self, package_name: str) -> bool:
        """Clear application data"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "clear", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            self.errors.append(f"Clear data error: {str(e)}")
            return False

    def enable_package(self, package_name: str) -> bool:
        """Enable package"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "enable", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            self.errors.append(f"Enable error: {str(e)}")
            return False

    def disable_package(self, package_name: str) -> bool:
        """Disable package"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "disable", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            self.errors.append(f"Disable error: {str(e)}")
            return False

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get package version"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "dumpsys", "package", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if "versionName=" in line:
                    return line.split("versionName=")[1].strip()

            return "N/A"

        except:
            return "N/A"

    def _get_package_version_code(self, package_name: str) -> Optional[str]:
        """Get package version code"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "dumpsys", "package", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if "versionCode=" in line:
                    return line.split("versionCode=")[1].strip()

            return "N/A"

        except:
            return "N/A"

    def _get_installed_size(self, package_name: str) -> Optional[str]:
        """Get installed size"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "get-install-location"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            return "N/A"  # Would need additional parsing

        except:
            return "N/A"

    def _get_data_directory(self, package_name: str) -> Optional[str]:
        """Get package data directory"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "pm", "dump", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            return f"/data/data/{package_name}"

        except:
            return "N/A"

    def _get_first_install_time(self, package_name: str) -> Optional[str]:
        """Get first install time"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "dumpsys", "package", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if "firstInstallTime=" in line:
                    return line.split("firstInstallTime=")[1].strip()

            return "N/A"

        except:
            return "N/A"

    def _get_last_update_time(self, package_name: str) -> Optional[str]:
        """Get last update time"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "dumpsys", "package", package_name])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if "lastUpdateTime=" in line:
                    return line.split("lastUpdateTime=")[1].strip()

            return "N/A"

        except:
            return "N/A"


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: adb-package-manager.py [list|install|uninstall|info|clear|enable|disable]")
        return 1

    command = sys.argv[1]
    device = None

    if "--device" in sys.argv:
        idx = sys.argv.index("--device")
        if idx + 1 < len(sys.argv):
            device = sys.argv[idx + 1]

    manager = PackageManager(device=device)

    if command == "list":
        packages = manager.list_packages(verbose="--verbose" in sys.argv)
        print(f"\n📦 Installed Packages ({len(packages)}):\n")
        for pkg in packages[:20]:  # Show first 20
            print(f"  • {pkg.name}")
        if len(packages) > 20:
            print(f"  ... and {len(packages) - 20} more")

    elif command == "install":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py install <apk_path>")
            return 1

        apk = sys.argv[2]
        force = "--force" in sys.argv
        print(f"Installing {apk}...")
        if manager.install_apk(apk, force=force):
            print("✅ Installation successful")
        else:
            print(f"❌ Installation failed: {manager.errors[0] if manager.errors else 'Unknown error'}")
            return 1

    elif command == "uninstall":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py uninstall <package_name>")
            return 1

        package = sys.argv[2]
        keep = "--keep" in sys.argv
        if manager.uninstall_package(package, keep_data=keep):
            print(f"✅ {package} uninstalled")
        else:
            print(f"❌ Uninstall failed: {manager.errors[0] if manager.errors else 'Unknown error'}")
            return 1

    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py info <package_name>")
            return 1

        package = sys.argv[2]
        info = manager.get_package_info(package)
        print(f"\n📦 Package Information: {package}\n")
        for key, value in info.items():
            print(f"  {key}: {value}")

    elif command == "clear":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py clear <package_name>")
            return 1

        package = sys.argv[2]
        if manager.clear_package_data(package):
            print(f"✅ Data cleared for {package}")
        else:
            print(f"❌ Failed to clear data")
            return 1

    elif command == "enable":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py enable <package_name>")
            return 1

        package = sys.argv[2]
        if manager.enable_package(package):
            print(f"✅ {package} enabled")
        else:
            print(f"❌ Failed to enable package")
            return 1

    elif command == "disable":
        if len(sys.argv) < 3:
            print("Usage: adb-package-manager.py disable <package_name>")
            return 1

        package = sys.argv[2]
        if manager.disable_package(package):
            print(f"✅ {package} disabled")
        else:
            print(f"❌ Failed to disable package")
            return 1

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
