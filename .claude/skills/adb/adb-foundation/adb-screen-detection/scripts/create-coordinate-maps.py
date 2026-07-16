#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Create Coordinate Maps for Different Resolutions

Generates resolution-specific coordinate mapping files for UI element automation
across different device resolutions. Maps elements from one resolution to another
using scaling calculations.

Usage:
    uv run create-coordinate-maps.py --device localhost:5555
    uv run create-coordinate-maps.py --device localhost:5555 --output ./coord_maps
    uv run create-coordinate-maps.py --device localhost:5555 --capture-elements

Exit Codes:
    0 - Success (maps created)
    1 - Warning (partial maps)
    2 - Error (map creation failed)
    3 - Critical (device error)
"""

import click
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple


@dataclass
class CoordinateMap:
    """Coordinate mapping for a specific resolution"""
    source_resolution: Tuple[int, int]
    target_resolution: Tuple[int, int]
    scale_x: float
    scale_y: float
    elements: Dict[str, Dict] = None

    def __post_init__(self):
        if self.elements is None:
            self.elements = {}


def connect_device(device_id: str):
    """Connect to device via uiautomator2"""
    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)
        return device
    except Exception as e:
        return None


def get_device_resolution(device) -> Optional[Tuple[int, int]]:
    """Get device screen resolution"""
    try:
        info = device.info
        width = info.get('displayWidth', 0)
        height = info.get('displayHeight', 0)
        return (width, height)
    except Exception:
        return None


def capture_element_coordinates(device, element_name: str) -> Optional[Dict]:
    """
    Capture coordinates of an element.

    Returns:
        Dictionary with element info and coordinates
    """
    try:
        selector = device(text=element_name)
        if not selector.wait(timeout=3):
            return None

        info = selector.info
        bounds = info.get('bounds', {})

        return {
            'name': element_name,
            'bounds': bounds,
            'center_x': bounds.get('left', 0) + (bounds.get('right', 0) - bounds.get('left', 0)) // 2,
            'center_y': bounds.get('top', 0) + (bounds.get('bottom', 0) - bounds.get('top', 0)) // 2,
            'width': bounds.get('right', 0) - bounds.get('left', 0),
            'height': bounds.get('bottom', 0) - bounds.get('top', 0),
        }
    except Exception:
        return None


def scale_coordinates(coords: Dict, scale_x: float, scale_y: float) -> Dict:
    """
    Scale coordinates from one resolution to another.

    Args:
        coords: Coordinate dictionary
        scale_x: X-axis scale factor
        scale_y: Y-axis scale factor

    Returns:
        Scaled coordinate dictionary
    """
    if coords is None:
        return None

    scaled = coords.copy()

    # Scale center coordinates
    if 'center_x' in coords:
        scaled['center_x'] = int(coords['center_x'] * scale_x)
    if 'center_y' in coords:
        scaled['center_y'] = int(coords['center_y'] * scale_y)

    # Scale bounds
    if 'bounds' in coords:
        bounds = coords['bounds']
        scaled['bounds'] = {
            'left': int(bounds.get('left', 0) * scale_x),
            'top': int(bounds.get('top', 0) * scale_y),
            'right': int(bounds.get('right', 0) * scale_x),
            'bottom': int(bounds.get('bottom', 0) * scale_y),
        }

    # Scale dimensions
    if 'width' in coords:
        scaled['width'] = int(coords['width'] * scale_x)
    if 'height' in coords:
        scaled['height'] = int(coords['height'] * scale_y)

    return scaled


@click.command()
@click.option('--device', type=str, default='localhost:5555', help='Device ID')
@click.option('--output', type=click.Path(), default='./coord_maps', help='Output directory')
@click.option('--capture-elements', is_flag=True, help='Capture element coordinates')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, output: str, capture_elements: bool, output_json: bool, verbose: bool) -> None:
    """
    Create coordinate maps for different device resolutions.
    """
    output_dir = Path(output)

    # Create output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        click.echo(f"✗ Error: Failed to create output directory: {e}", err=True)
        sys.exit(2)

    # Connect to device
    if verbose:
        click.echo(f"Connecting to device: {device}", err=True)

    d = connect_device(device)
    if d is None:
        click.echo(f"✗ Error: Failed to connect to device {device}", err=True)
        sys.exit(3)

    try:
        # Get source device resolution
        source_res = get_device_resolution(d)
        if not source_res:
            click.echo("✗ Error: Failed to get device resolution", err=True)
            sys.exit(3)

        source_width, source_height = source_res

        if verbose:
            click.echo(f"Source device resolution: {source_width}x{source_height}", err=True)

        # Define target resolutions
        target_resolutions = [
            (1280, 720),    # 720p
            (1920, 1080),   # 1080p
            (2560, 1440),   # 1440p (usually source)
        ]

        maps_created = 0
        elements_captured = {}

        # Capture element coordinates if requested
        if capture_elements:
            if verbose:
                click.echo("Capturing element coordinates...", err=True)

            element_names = [
                "Install",
                "Method",
                "Options",
                "NEXT",
            ]

            for elem_name in element_names:
                coords = capture_element_coordinates(d, elem_name)
                if coords:
                    elements_captured[elem_name] = coords
                    if verbose:
                        click.echo(f"✓ Captured: {elem_name}", err=True)

        # Create maps for each target resolution
        for target_width, target_height in target_resolutions:
            map_data = {
                'source_resolution': source_res,
                'target_resolution': (target_width, target_height),
                'scale_x': target_width / source_width,
                'scale_y': target_height / source_height,
                'elements': {},
                'metadata': {
                    'description': f'Coordinate mapping from {source_width}x{source_height} to {target_width}x{target_height}',
                    'created_at': __import__('datetime').datetime.now().isoformat(),
                }
            }

            # Scale all captured elements
            for elem_name, coords in elements_captured.items():
                map_data['elements'][elem_name] = scale_coordinates(
                    coords,
                    map_data['scale_x'],
                    map_data['scale_y']
                )

            # Save map file
            map_filename = f"coord_map_{target_width}x{target_height}.json"
            map_path = output_dir / map_filename

            try:
                with open(map_path, 'w') as f:
                    json.dump(map_data, f, indent=2)
                maps_created += 1

                if verbose:
                    click.echo(f"✓ Created: {map_filename}", err=True)
            except Exception as e:
                click.echo(f"✗ Failed to save {map_filename}: {e}", err=True)

        # Create summary file
        summary = {
            'source_resolution': source_res,
            'target_resolutions': target_resolutions,
            'maps_created': maps_created,
            'elements_captured': len(elements_captured),
            'element_names': list(elements_captured.keys()),
        }

        summary_path = output_dir / "coordinate_maps_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Output result
        click.echo("\n" + "="*60)
        click.echo("✓ Coordinate Maps Created")
        click.echo("="*60)
        click.echo(f"Source resolution: {source_width}x{source_height}")
        click.echo(f"Maps created: {maps_created}/{len(target_resolutions)}")
        click.echo(f"Elements captured: {len(elements_captured)}")
        click.echo(f"Output directory: {output_dir}")
        click.echo("\nGenerated files:")
        for res in target_resolutions:
            click.echo(f"  - coord_map_{res[0]}x{res[1]}.json")
        click.echo(f"  - coordinate_maps_summary.json")
        click.echo("="*60)

        sys.exit(0)

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(2)


if __name__ == "__main__":
    cli()
