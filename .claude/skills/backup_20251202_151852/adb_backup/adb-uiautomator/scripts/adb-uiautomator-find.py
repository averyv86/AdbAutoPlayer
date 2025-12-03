#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Find UI Element - Semantic element detection via uiautomator2

Locate UI elements by resource ID, text, or class using accessibility tree.

Usage:
    uv run adb-uiautomator-find.py --device 127.0.0.1:5555 --text "로그인"
    uv run adb-uiautomator-find.py --device 127.0.0.1:5555 --resource-id "com.example:id/button"
    uv run adb-uiautomator-find.py --device 127.0.0.1:5555 --class-name "android.widget.Button"

Exit Codes:
    0 - Success (element found)
    1 - Warning (element not found)
    2 - Error (connection failed)
    3 - Critical (invalid parameters)
"""

import click
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class ElementResult:
    """Result of element search"""
    found: bool
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    text: Optional[str] = None
    resource_id: Optional[str] = None
    class_name: Optional[str] = None
    content_desc: Optional[str] = None
    error: Optional[str] = None

def connect_device(device_id: str):
    """Connect to device via uiautomator2"""
    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)
        return device
    except Exception as e:
        return None

@click.command()
@click.option('--device', type=str, default='127.0.0.1:5555', help='Device ID')
@click.option('--text', type=str, help='Find by text content')
@click.option('--resource-id', type=str, help='Find by resource ID')
@click.option('--class-name', type=str, help='Find by class name')
@click.option('--content-desc', type=str, help='Find by content description')
@click.option('--timeout', type=int, default=10, help='Timeout in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, text: Optional[str], resource_id: Optional[str],
        class_name: Optional[str], content_desc: Optional[str],
        timeout: int, output_json: bool, verbose: bool) -> None:
    """
    Find UI element using uiautomator2 semantic detection.
    """
    # Validate parameters
    if not any([text, resource_id, class_name, content_desc]):
        result = ElementResult(
            found=False,
            error="Must specify at least one search parameter: --text, --resource-id, --class-name, or --content-desc"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {result.error}", err=True)
        sys.exit(3)

    # Connect to device
    if verbose:
        click.echo(f"Connecting to device: {device}", err=True)

    try:
        import uiautomator2 as u2
    except ImportError:
        result = ElementResult(
            found=False,
            error="uiautomator2 not installed. Install with: pip install uiautomator2"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {result.error}", err=True)
        sys.exit(2)

    d = connect_device(device)
    if d is None:
        result = ElementResult(
            found=False,
            error=f"Failed to connect to device {device}"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {result.error}", err=True)
        sys.exit(2)

    try:
        if verbose:
            click.echo(f"Searching for element with timeout={timeout}s", err=True)

        element = None
        element_info = None

        # Try to find element using specified criteria
        if text:
            try:
                selector = d(text=text)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Found element by text: {text}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Failed to find element by text: {e}", err=True)

        if not element and resource_id:
            try:
                selector = d(resourceId=resource_id)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Found element by resource ID: {resource_id}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Failed to find element by resource ID: {e}", err=True)

        if not element and class_name:
            try:
                selector = d(className=class_name)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Found element by class name: {class_name}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Failed to find element by class name: {e}", err=True)

        if not element and content_desc:
            try:
                selector = d(description=content_desc)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Found element by content description: {content_desc}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Failed to find element by content description: {e}", err=True)

        # Build result
        if element and element_info:
            result = ElementResult(
                found=True,
                x=element_info.get('bounds', {}).get('left', 0) +
                  (element_info.get('bounds', {}).get('right', 0) -
                   element_info.get('bounds', {}).get('left', 0)) // 2,
                y=element_info.get('bounds', {}).get('top', 0) +
                  (element_info.get('bounds', {}).get('bottom', 0) -
                   element_info.get('bounds', {}).get('top', 0)) // 2,
                width=element_info.get('bounds', {}).get('right', 0) -
                      element_info.get('bounds', {}).get('left', 0),
                height=element_info.get('bounds', {}).get('bottom', 0) -
                       element_info.get('bounds', {}).get('top', 0),
                text=element_info.get('text'),
                resource_id=element_info.get('resourceId'),
                class_name=element_info.get('className'),
                content_desc=element_info.get('contentDescription')
            )
            exit_code = 0
        else:
            result = ElementResult(
                found=False,
                error="Element not found within timeout"
            )
            exit_code = 1

        # Output result
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            if result.found:
                click.echo(f"✓ Element found at: ({result.x}, {result.y})")
                if result.text:
                    click.echo(f"  Text: {result.text}")
                if result.resource_id:
                    click.echo(f"  Resource ID: {result.resource_id}")
            else:
                click.echo(f"✗ Element not found", err=True)
                if result.error:
                    click.echo(f"  Error: {result.error}", err=True)

        sys.exit(exit_code)

    except Exception as e:
        result = ElementResult(
            found=False,
            error=str(e)
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(2)

if __name__ == "__main__":
    cli()
