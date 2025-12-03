#!/usr/bin/env python3
"""Resolution-Aware Tap Infrastructure for ADB Automation.

This module provides reliable tap functionality with:
1. Resolution detection (Override vs Physical size)
2. Element finding via UIAutomator dump
3. State verification after taps
4. Retry logic with backoff

Created based on live testing on Samsung SM-S908E (2560x1440).

Key Discovery: Samsung devices may use Override size for display scaling.
The `input tap` command must use the effective resolution coordinates.
"""

import subprocess
import time
import re
import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum


class TapResult(Enum):
    """Result of a tap operation."""
    SUCCESS = "success"  # Tap executed and state changed
    NO_STATE_CHANGE = "no_state_change"  # Tap executed but UI didn't change
    ELEMENT_NOT_FOUND = "element_not_found"  # Target element not found
    TIMEOUT = "timeout"  # Operation timed out
    ERROR = "error"  # General error


@dataclass
class Resolution:
    """Device display resolution."""
    width: int
    height: int
    is_override: bool = False
    density: int = 0


@dataclass
class ElementBounds:
    """UI element bounding box."""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates of the element."""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1


@dataclass
class UIElement:
    """Represents a UI element from UIAutomator dump."""
    text: str
    resource_id: str
    class_name: str
    bounds: ElementBounds
    clickable: bool
    enabled: bool
    content_desc: str = ""

    def __str__(self) -> str:
        return f"UIElement(text='{self.text}', bounds={self.bounds.center})"


class ResolutionAwareTap:
    """Provides resolution-aware tap functionality with state verification.

    Usage:
        tap_controller = ResolutionAwareTap(device_id="localhost:5555")

        # Find and tap element by text
        result = tap_controller.find_and_tap("Install")

        # Tap with state verification
        result = tap_controller.tap_with_verification(x=2400, y=257)

        # Wait for text to appear and tap it
        result = tap_controller.wait_and_tap("Direct Install", timeout=10)
    """

    def __init__(self, device_id: str = "localhost:5555"):
        """Initialize with device ID.

        Args:
            device_id: ADB device identifier (e.g., "localhost:5555")
        """
        self.device_id = device_id
        self._resolution: Optional[Resolution] = None
        self._last_ui_dump: str = ""
        self._last_ui_hash: str = ""

    def adb(self, cmd: str, timeout: int = 30) -> str:
        """Run ADB command and return output.

        Args:
            cmd: ADB command (without 'adb -s device' prefix)
            timeout: Command timeout in seconds

        Returns:
            Command stdout output
        """
        full_cmd = f"adb -s {self.device_id} {cmd}"
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return ""

    def shell(self, cmd: str, timeout: int = 30) -> str:
        """Run ADB shell command.

        Args:
            cmd: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Command output
        """
        # Escape double quotes in the command
        escaped_cmd = cmd.replace('"', '\\"')
        return self.adb(f'shell "{escaped_cmd}"', timeout)

    def get_resolution(self, force_refresh: bool = False) -> Resolution:
        """Get device display resolution.

        Checks for Override size first (used by Samsung for display scaling),
        then falls back to Physical size.

        Args:
            force_refresh: If True, re-query the device

        Returns:
            Resolution dataclass with width, height, and is_override flag
        """
        if self._resolution and not force_refresh:
            return self._resolution

        # Get size info
        size_output = self.shell("wm size")

        # Check for Override size first (Samsung display scaling)
        override_match = re.search(r'Override size:\s*(\d+)x(\d+)', size_output)
        physical_match = re.search(r'Physical size:\s*(\d+)x(\d+)', size_output)

        if override_match:
            width, height = map(int, override_match.groups())
            is_override = True
        elif physical_match:
            width, height = map(int, physical_match.groups())
            is_override = False
        else:
            # Default fallback
            width, height = 1080, 1920
            is_override = False

        # Get density
        density_output = self.shell("wm density")
        density_match = re.search(r'Physical density:\s*(\d+)', density_output)
        density = int(density_match.group(1)) if density_match else 0

        self._resolution = Resolution(
            width=width,
            height=height,
            is_override=is_override,
            density=density
        )
        return self._resolution

    def get_ui_dump(self, force_refresh: bool = True) -> str:
        """Get UIAutomator hierarchy dump.

        Args:
            force_refresh: If True, always get fresh dump

        Returns:
            XML string of UI hierarchy
        """
        if not force_refresh and self._last_ui_dump:
            return self._last_ui_dump

        # Dump UI hierarchy to device
        self.shell("uiautomator dump /sdcard/ui_dump.xml")
        # Read the dump
        xml_content = self.shell("cat /sdcard/ui_dump.xml")

        self._last_ui_dump = xml_content
        self._last_ui_hash = hashlib.md5(xml_content.encode()).hexdigest()

        return xml_content

    def get_ui_hash(self) -> str:
        """Get hash of current UI state for change detection.

        Returns:
            MD5 hash of current UI dump
        """
        ui_dump = self.get_ui_dump(force_refresh=True)
        return hashlib.md5(ui_dump.encode()).hexdigest()

    def find_element_by_text(
        self,
        target_text: str,
        exact_match: bool = False,
        ui_xml: Optional[str] = None
    ) -> Optional[UIElement]:
        """Find UI element by text content.

        Args:
            target_text: Text to search for
            exact_match: If True, require exact text match
            ui_xml: Optional pre-fetched UI dump

        Returns:
            UIElement if found, None otherwise
        """
        if ui_xml is None:
            ui_xml = self.get_ui_dump()

        # Build regex pattern based on match type
        if exact_match:
            pattern = rf'text="{re.escape(target_text)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        else:
            pattern = rf'text="[^"]*{re.escape(target_text)}[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'

        match = re.search(pattern, ui_xml, re.IGNORECASE)

        if match:
            x1, y1, x2, y2 = map(int, match.groups())

            # Extract additional attributes
            node_pattern = rf'<node[^>]*text="[^"]*{re.escape(target_text)}[^"]*"[^>]*>'
            node_match = re.search(node_pattern, ui_xml, re.IGNORECASE)

            clickable = 'clickable="true"' in (node_match.group(0) if node_match else "")
            enabled = 'enabled="true"' in (node_match.group(0) if node_match else "")

            # Get resource-id
            rid_match = re.search(r'resource-id="([^"]*)"', node_match.group(0) if node_match else "")
            resource_id = rid_match.group(1) if rid_match else ""

            # Get class
            class_match = re.search(r'class="([^"]*)"', node_match.group(0) if node_match else "")
            class_name = class_match.group(1) if class_match else ""

            return UIElement(
                text=target_text,
                resource_id=resource_id,
                class_name=class_name,
                bounds=ElementBounds(x1, y1, x2, y2),
                clickable=clickable,
                enabled=enabled
            )

        return None

    def find_element_by_resource_id(
        self,
        resource_id: str,
        ui_xml: Optional[str] = None
    ) -> Optional[UIElement]:
        """Find UI element by resource ID.

        Args:
            resource_id: Resource ID to search for (e.g., "com.app:id/button")
            ui_xml: Optional pre-fetched UI dump

        Returns:
            UIElement if found, None otherwise
        """
        if ui_xml is None:
            ui_xml = self.get_ui_dump()

        pattern = rf'resource-id="{re.escape(resource_id)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        match = re.search(pattern, ui_xml)

        if match:
            x1, y1, x2, y2 = map(int, match.groups())

            # Extract text
            node_pattern = rf'<node[^>]*resource-id="{re.escape(resource_id)}"[^>]*>'
            node_match = re.search(node_pattern, ui_xml)

            text_match = re.search(r'text="([^"]*)"', node_match.group(0) if node_match else "")
            text = text_match.group(1) if text_match else ""

            clickable = 'clickable="true"' in (node_match.group(0) if node_match else "")
            enabled = 'enabled="true"' in (node_match.group(0) if node_match else "")

            class_match = re.search(r'class="([^"]*)"', node_match.group(0) if node_match else "")
            class_name = class_match.group(1) if class_match else ""

            return UIElement(
                text=text,
                resource_id=resource_id,
                class_name=class_name,
                bounds=ElementBounds(x1, y1, x2, y2),
                clickable=clickable,
                enabled=enabled
            )

        return None

    def tap(self, x: int, y: int) -> None:
        """Execute tap at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.shell(f"input tap {x} {y}")

    def tap_with_verification(
        self,
        x: int,
        y: int,
        timeout: float = 3.0,
        settle_time: float = 0.5
    ) -> TapResult:
        """Tap and verify that screen state changed.

        Args:
            x: X coordinate
            y: Y coordinate
            timeout: Maximum time to wait for state change
            settle_time: Time to wait after tap before checking

        Returns:
            TapResult indicating success or failure mode
        """
        # Get state before tap
        before_hash = self.get_ui_hash()

        # Execute tap
        self.tap(x, y)

        # Wait for UI to settle
        time.sleep(settle_time)

        # Check for state change with retries
        start_time = time.time()
        while time.time() - start_time < timeout:
            after_hash = self.get_ui_hash()
            if after_hash != before_hash:
                return TapResult.SUCCESS
            time.sleep(0.3)

        return TapResult.NO_STATE_CHANGE

    def find_and_tap(
        self,
        target_text: str,
        timeout: int = 5,
        verify_state_change: bool = True,
        exact_match: bool = False
    ) -> TapResult:
        """Find element by text and tap it.

        Args:
            target_text: Text to find and tap
            timeout: Maximum time to search for element
            verify_state_change: If True, verify UI changed after tap
            exact_match: If True, require exact text match

        Returns:
            TapResult indicating success or failure mode
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            element = self.find_element_by_text(target_text, exact_match=exact_match)

            if element:
                center_x, center_y = element.bounds.center

                if verify_state_change:
                    return self.tap_with_verification(center_x, center_y)
                else:
                    self.tap(center_x, center_y)
                    return TapResult.SUCCESS

            time.sleep(0.5)

        return TapResult.ELEMENT_NOT_FOUND

    def wait_for_text(
        self,
        target_text: str,
        timeout: int = 10,
        exact_match: bool = False
    ) -> bool:
        """Wait for text to appear on screen.

        Args:
            target_text: Text to wait for
            timeout: Maximum time to wait
            exact_match: If True, require exact text match

        Returns:
            True if text appeared, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            element = self.find_element_by_text(target_text, exact_match=exact_match)
            if element:
                return True
            time.sleep(0.5)

        return False

    def wait_and_tap(
        self,
        target_text: str,
        timeout: int = 10,
        verify_state_change: bool = True,
        exact_match: bool = False
    ) -> TapResult:
        """Wait for text to appear, then tap it.

        Args:
            target_text: Text to wait for and tap
            timeout: Maximum time to wait
            verify_state_change: If True, verify UI changed after tap
            exact_match: If True, require exact text match

        Returns:
            TapResult indicating success or failure mode
        """
        if self.wait_for_text(target_text, timeout, exact_match):
            return self.find_and_tap(
                target_text,
                timeout=3,
                verify_state_change=verify_state_change,
                exact_match=exact_match
            )
        return TapResult.TIMEOUT

    def get_all_text_elements(self, ui_xml: Optional[str] = None) -> List[UIElement]:
        """Get all UI elements with text.

        Args:
            ui_xml: Optional pre-fetched UI dump

        Returns:
            List of UIElement objects with text content
        """
        if ui_xml is None:
            ui_xml = self.get_ui_dump()

        elements = []
        pattern = r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'

        for match in re.finditer(pattern, ui_xml):
            text, x1, y1, x2, y2 = match.groups()
            if text:  # Skip empty text
                elements.append(UIElement(
                    text=text,
                    resource_id="",
                    class_name="",
                    bounds=ElementBounds(int(x1), int(y1), int(x2), int(y2)),
                    clickable=False,
                    enabled=True
                ))

        return elements

    def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration_ms: int = 300
    ) -> None:
        """Perform swipe gesture.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration_ms: Swipe duration in milliseconds
        """
        self.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def keyevent(self, key: str) -> None:
        """Send key event.

        Args:
            key: Key name (e.g., "KEYCODE_BACK", "KEYCODE_HOME")
        """
        self.shell(f"input keyevent {key}")

    def back(self) -> None:
        """Press back button."""
        self.keyevent("KEYCODE_BACK")

    def home(self) -> None:
        """Press home button."""
        self.keyevent("KEYCODE_HOME")

    def screenshot(self, local_path: str = "/tmp/screenshot.png") -> str:
        """Take screenshot and save locally.

        Args:
            local_path: Path to save screenshot

        Returns:
            Path to saved screenshot
        """
        subprocess.run(
            f"adb -s {self.device_id} exec-out screencap -p > {local_path}",
            shell=True
        )
        return local_path


# Convenience functions for direct use
def create_tap_controller(device_id: str = "localhost:5555") -> ResolutionAwareTap:
    """Create a ResolutionAwareTap instance.

    Args:
        device_id: ADB device identifier

    Returns:
        Configured ResolutionAwareTap instance
    """
    return ResolutionAwareTap(device_id)


if __name__ == "__main__":
    # Demo/test usage
    print("ResolutionAwareTap - Demo")
    print("=" * 50)

    controller = ResolutionAwareTap("localhost:5555")

    # Get resolution
    res = controller.get_resolution()
    print(f"Resolution: {res.width}x{res.height}")
    print(f"Override size: {res.is_override}")
    print(f"Density: {res.density}")

    # Get UI elements
    elements = controller.get_all_text_elements()
    print(f"\nFound {len(elements)} text elements:")
    for elem in elements[:10]:
        print(f"  - '{elem.text}' at {elem.bounds.center}")

    print("\nDemo complete!")
