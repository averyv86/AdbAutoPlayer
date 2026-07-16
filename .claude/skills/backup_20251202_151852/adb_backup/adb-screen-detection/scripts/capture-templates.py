#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pillow>=10.0.0",
#     "opencv-python>=4.8.0",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Capture Template Images from Device

Captures UI element templates from a connected Android device for use in
template matching automation. Extracts element bounds from accessibility tree
and saves cropped images.

Usage:
    uv run capture-templates.py --device localhost:5555 --element-text "Login"
    uv run capture-templates.py --device localhost:5555 --element-class android.widget.Button
    uv run capture-templates.py --device localhost:5555 --output ./templates/ --capture-all

Exit Codes:
    0 - Success (templates captured)
    1 - Warning (partial capture)
    2 - Error (capture failed)
    3 - Critical (device error)
"""

import click
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List
import cv2
import numpy as np
from PIL import Image

@dataclass
class CaptureResult:
    """Result of template capture operation"""
    success: bool
    templates_captured: int = 0
    elements_found: int = 0
    output_dir: Optional[str] = None
    captured_files: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.captured_files is None:
            self.captured_files = []


def connect_device(device_id: str):
    """Connect to device via uiautomator2"""
    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)
        return device
    except Exception as e:
        return None


def capture_element_template(device, selector_text: str, output_dir: Path) -> Optional[str]:
    """
    Capture template for element by text.

    Returns:
        Path to saved template or None if failed
    """
    try:
        # Get screenshot as numpy array
        img = device.screenshot()
        img_array = np.array(img)

        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Find element by text
        selector = device(text=selector_text)
        if not selector.wait(timeout=5):
            return None

        info = selector.info
        bounds = info.get('bounds', {})

        if not bounds:
            return None

        # Extract element region
        left = bounds.get('left', 0)
        top = bounds.get('top', 0)
        right = bounds.get('right', 0)
        bottom = bounds.get('bottom', 0)

        if left >= right or top >= bottom:
            return None

        # Crop element from screenshot
        element_img = img_bgr[top:bottom, left:right]

        if element_img.size == 0:
            return None

        # Save template
        safe_name = "".join(c if c.isalnum() else "_" for c in selector_text)
        output_path = output_dir / f"template_{safe_name}.png"

        cv2.imwrite(str(output_path), element_img)
        return str(output_path)

    except Exception as e:
        return None


def capture_element_by_class(device, class_name: str, output_dir: Path,
                            count: int = 1) -> List[str]:
    """
    Capture multiple elements by class name.

    Returns:
        List of saved template paths
    """
    saved_paths = []
    try:
        # Get screenshot
        img = device.screenshot()
        img_array = np.array(img)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Find all elements of class
        selector = device(className=class_name)

        captured = 0
        for i in range(10):  # Try up to 10 elements
            if captured >= count:
                break

            try:
                # Get element by instance
                element = device(className=class_name, instance=i)
                if not element.exists():
                    continue

                info = element.info
                bounds = info.get('bounds', {})
                text = info.get('text', '')

                if not bounds or (bounds.get('left', 0) >= bounds.get('right', 0)):
                    continue

                # Crop element
                left = bounds.get('left', 0)
                top = bounds.get('top', 0)
                right = bounds.get('right', 0)
                bottom = bounds.get('bottom', 0)

                element_img = img_bgr[top:bottom, left:right]

                if element_img.size == 0:
                    continue

                # Save template
                safe_text = "".join(c if c.isalnum() else "_" for c in text[:20]) if text else f"instance_{i}"
                output_path = output_dir / f"template_{safe_text}_{i}.png"

                cv2.imwrite(str(output_path), element_img)
                saved_paths.append(str(output_path))
                captured += 1

            except Exception:
                continue

        return saved_paths

    except Exception as e:
        return []


@click.command()
@click.option('--device', type=str, default='localhost:5555', help='Device ID')
@click.option('--element-text', type=str, help='Capture element by text')
@click.option('--element-class', type=str, help='Capture elements by class name')
@click.option('--output', type=click.Path(), default='./templates', help='Output directory')
@click.option('--capture-all', is_flag=True, help='Capture all UI elements')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, element_text: Optional[str], element_class: Optional[str],
        output: str, capture_all: bool, output_json: bool, verbose: bool) -> None:
    """
    Capture template images from device for template matching automation.
    """
    result = CaptureResult(success=False)
    output_dir = Path(output)

    # Create output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        result.output_dir = str(output_dir)
    except Exception as e:
        result.error = f"Failed to create output directory: {e}"
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {result.error}", err=True)
        sys.exit(2)

    # Connect to device
    if verbose:
        click.echo(f"Connecting to device: {device}", err=True)

    d = connect_device(device)
    if d is None:
        result.error = f"Failed to connect to device {device}"
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {result.error}", err=True)
        sys.exit(3)

    try:
        # Capture by specific text
        if element_text:
            if verbose:
                click.echo(f"Capturing element with text: {element_text}", err=True)

            path = capture_element_template(d, element_text, output_dir)
            if path:
                result.captured_files.append(path)
                result.templates_captured += 1
                if verbose:
                    click.echo(f"✓ Saved: {path}", err=True)
            else:
                if verbose:
                    click.echo(f"✗ Failed to capture element with text: {element_text}", err=True)

        # Capture by class
        elif element_class:
            if verbose:
                click.echo(f"Capturing elements of class: {element_class}", err=True)

            paths = capture_element_by_class(d, element_class, output_dir, count=5)
            if paths:
                result.captured_files.extend(paths)
                result.templates_captured += len(paths)
                result.elements_found += len(paths)
                if verbose:
                    for path in paths:
                        click.echo(f"✓ Saved: {path}", err=True)
            else:
                if verbose:
                    click.echo(f"✗ Failed to capture elements of class: {element_class}", err=True)

        # Capture all visible elements
        elif capture_all:
            if verbose:
                click.echo("Capturing all UI elements...", err=True)

            # Common element types to capture
            element_classes = [
                "android.widget.Button",
                "android.widget.EditText",
                "android.widget.TextView",
                "android.widget.ImageButton",
            ]

            for elem_class in element_classes:
                if verbose:
                    click.echo(f"  Scanning {elem_class}...", err=True)

                paths = capture_element_by_class(d, elem_class, output_dir, count=3)
                result.captured_files.extend(paths)
                result.templates_captured += len(paths)
                result.elements_found += len(paths)

        else:
            result.error = "Must specify --element-text, --element-class, or --capture-all"
            if output_json:
                click.echo(json.dumps(asdict(result)))
            else:
                click.echo(f"✗ Error: {result.error}", err=True)
            sys.exit(2)

        result.success = result.templates_captured > 0

        # Output result
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo("\n" + "="*60)
            click.echo("✓ Template Capture Complete")
            click.echo("="*60)
            click.echo(f"Templates captured: {result.templates_captured}")
            click.echo(f"Elements found: {result.elements_found}")
            click.echo(f"Output directory: {result.output_dir}")
            if result.captured_files:
                click.echo(f"\nCaptured files:")
                for f in result.captured_files:
                    click.echo(f"  - {Path(f).name}")
            click.echo("="*60)

        sys.exit(0 if result.success else 1)

    except Exception as e:
        result.error = str(e)
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(2)


if __name__ == "__main__":
    cli()
