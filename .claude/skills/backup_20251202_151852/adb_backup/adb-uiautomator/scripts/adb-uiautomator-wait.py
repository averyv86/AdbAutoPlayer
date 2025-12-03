#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Wait for UI Element - Semantic element waiting via uiautomator2

Wait for UI elements to appear by resource ID, text, or class using accessibility tree.

Usage:
    uv run adb-uiautomator-wait.py --device 127.0.0.1:5555 --text "로그인" --timeout 10
    uv run adb-uiautomator-wait.py --device 127.0.0.1:5555 --resource-id "com.example:id/button"
    uv run adb-uiautomator-wait.py --device 127.0.0.1:5555 --text "홈" --timeout 5

Exit Codes:
    0 - Success (element appeared)
    1 - Warning (element did not appear)
    2 - Error (connection failed)
    3 - Critical (invalid parameters)
"""

import click
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class WaitResult:
    """Result of wait operation"""
    success: bool
    appeared: bool = False
    text: Optional[str] = None
    resource_id: Optional[str] = None
    timeout: Optional[int] = None
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
@click.option('--text', type=str, help='Wait for element by text content')
@click.option('--resource-id', type=str, help='Wait for element by resource ID')
@click.option('--class-name', type=str, help='Wait for element by class name')
@click.option('--content-desc', type=str, help='Wait for element by content description')
@click.option('--timeout', type=int, default=10, help='Timeout in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, text: Optional[str], resource_id: Optional[str],
        class_name: Optional[str], content_desc: Optional[str],
        timeout: int, output_json: bool, verbose: bool) -> None:
    """
    Wait for UI element using uiautomator2 semantic detection.
    """
    # Validate parameters
    if not any([text, resource_id, class_name, content_desc]):
        result = WaitResult(
            success=False,
            appeared=False,
            timeout=timeout,
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
        result = WaitResult(
            success=False,
            appeared=False,
            timeout=timeout,
            error="uiautomator2 not installed. Install with: pip install uiautomator2"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {result.error}", err=True)
        sys.exit(2)

    d = connect_device(device)
    if d is None:
        result = WaitResult(
            success=False,
            appeared=False,
            timeout=timeout,
            error=f"Failed to connect to device {device}"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {result.error}", err=True)
        sys.exit(2)

    try:
        if verbose:
            click.echo(f"Waiting for element with timeout={timeout}s", err=True)

        element = None
        element_info = None

        # Try to wait for element using specified criteria
        if text:
            try:
                selector = d(text=text)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Element appeared: {text}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Element did not appear (text): {e}", err=True)

        if not element and resource_id:
            try:
                selector = d(resourceId=resource_id)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Element appeared: {resource_id}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Element did not appear (resource_id): {e}", err=True)

        if not element and class_name:
            try:
                selector = d(className=class_name)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Element appeared: {class_name}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Element did not appear (class_name): {e}", err=True)

        if not element and content_desc:
            try:
                selector = d(description=content_desc)
                if selector.wait(timeout=timeout):
                    element = selector
                    element_info = selector.info
                    if verbose:
                        click.echo(f"Element appeared: {content_desc}", err=True)
            except Exception as e:
                if verbose:
                    click.echo(f"Element did not appear (content_desc): {e}", err=True)

        # Build result
        if element and element_info:
            result = WaitResult(
                success=True,
                appeared=True,
                text=element_info.get('text'),
                resource_id=element_info.get('resourceId'),
                timeout=timeout
            )
            exit_code = 0
        else:
            result = WaitResult(
                success=False,
                appeared=False,
                text=text,
                resource_id=resource_id,
                timeout=timeout,
                error="Element did not appear within timeout"
            )
            exit_code = 1

        # Output result
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            if result.appeared:
                click.echo(f"✓ Element appeared within {timeout}s")
                if result.text:
                    click.echo(f"  Text: {result.text}")
                if result.resource_id:
                    click.echo(f"  Resource ID: {result.resource_id}")
            else:
                click.echo(f"✗ Element did not appear after {timeout}s", err=True)
                if result.error:
                    click.echo(f"  Error: {result.error}", err=True)

        sys.exit(exit_code)

    except Exception as e:
        result = WaitResult(
            success=False,
            appeared=False,
            timeout=timeout,
            error=str(e)
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(2)

if __name__ == "__main__":
    cli()
