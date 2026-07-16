#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Native Messaging Host for MoAI Tab Suspender

Bridges macOS Resource Optimizer with Chrome extension for tab suspension.
Uses Chrome Native Messaging protocol (JSON over stdio with length prefix).

Usage:
    # Normal mode (stdio communication with extension)
    uv run scripts/tab_suspender.py

    # Test mode (check configuration)
    uv run scripts/tab_suspender.py --test

    # Suspend tabs directly (for testing)
    uv run scripts/tab_suspender.py --suspend --browser=chrome

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

import json
import struct
import sys
import time
from pathlib import Path


def send_message(message: dict):
    """
    Send message to Chrome extension using Native Messaging protocol.

    Args:
        message: Dictionary to send as JSON
    """
    encoded = json.dumps(message).encode('utf-8')
    # Chrome expects: 4-byte length (little-endian) + JSON message
    sys.stdout.buffer.write(struct.pack('I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def receive_message() -> dict:
    """
    Receive message from Chrome extension.

    Returns:
        Dictionary parsed from JSON message
    """
    # Read 4-byte length prefix
    raw_length = sys.stdin.buffer.read(4)

    if not raw_length:
        # Connection closed
        sys.exit(0)

    # Unpack length (little-endian unsigned int)
    length = struct.unpack('I', raw_length)[0]

    # Read JSON message
    message_bytes = sys.stdin.buffer.read(length)
    message = message_bytes.decode('utf-8')

    return json.loads(message)


def handle_suspend_tabs():
    """
    Handle tab suspension request.

    Sends suspend_tabs action to extension and waits for response.
    """
    # Send suspend command
    send_message({
        'action': 'suspend_tabs',
        'timestamp': time.time()
    })

    # Wait for response
    response = receive_message()

    if response.get('success'):
        tabs_suspended = response.get('tabs_suspended', 0)
        tabs_total = response.get('tabs_total', 0)

        # Print TOON format result
        print(f"browser:Chrome|tabs:{tabs_total}|suspended:{tabs_suspended}|time:{time.time()}", file=sys.stderr)

        return response
    else:
        error = response.get('error', 'Unknown error')
        print(f"❌ Error: {error}", file=sys.stderr)
        return None


def handle_get_tab_count():
    """Get current tab count from extension."""
    send_message({'action': 'get_tab_count'})
    response = receive_message()
    return response


def test_connection():
    """
    Test Native Messaging connection.

    Returns:
        bool: True if connection successful
    """
    print("🔍 Testing Native Messaging Connection...", file=sys.stderr)

    # Check Native Messaging manifest exists
    manifest_paths = [
        Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json",
        Path.home() / "Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json",
    ]

    found = False
    for path in manifest_paths:
        if path.exists():
            print(f"✅ Found Native Messaging manifest: {path}", file=sys.stderr)
            found = True

            # Validate manifest
            try:
                with open(path) as f:
                    manifest = json.load(f)

                if manifest.get('name') == 'com.moai.tab_suspender':
                    print(f"✅ Manifest valid: {manifest.get('name')}", file=sys.stderr)

                script_path = manifest.get('path')
                if Path(script_path).exists():
                    print(f"✅ Host script exists: {script_path}", file=sys.stderr)
                else:
                    print(f"⚠️  Host script not found: {script_path}", file=sys.stderr)

            except Exception as e:
                print(f"❌ Error reading manifest: {e}", file=sys.stderr)

    if not found:
        print("❌ No Native Messaging manifest found", file=sys.stderr)
        print("Run install.sh to configure", file=sys.stderr)
        return False

    # Try to send ping
    try:
        send_message({'action': 'ping'})
        response = receive_message()

        if response.get('action') == 'pong':
            print("✅ Extension connection successful", file=sys.stderr)
            return True
        else:
            print(f"⚠️  Unexpected response: {response}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Native Messaging Host for MoAI Tab Suspender',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--test', action='store_true',
                       help='Test Native Messaging configuration')
    parser.add_argument('--suspend', action='store_true',
                       help='Suspend tabs (for testing)')
    parser.add_argument('--browser', default='chrome',
                       choices=['chrome', 'dia'],
                       help='Browser to target')

    args = parser.parse_args()

    if args.test:
        # Test mode
        success = test_connection()
        sys.exit(0 if success else 1)

    elif args.suspend:
        # Suspend tabs mode
        result = handle_suspend_tabs()
        sys.exit(0 if result else 1)

    else:
        # Normal mode: stdio communication loop
        # This is how Chrome extension calls the script

        try:
            while True:
                # Wait for message from extension
                message = receive_message()

                action = message.get('action')

                if action == 'suspend_tabs':
                    # Forward to extension
                    send_message(message)
                    # Extension will respond directly

                elif action == 'get_tab_count':
                    # Forward to extension
                    send_message(message)

                elif action == 'ping':
                    # Respond directly
                    send_message({'action': 'pong', 'timestamp': time.time()})

                else:
                    # Unknown action
                    send_message({
                        'success': False,
                        'error': f'Unknown action: {action}'
                    })

        except KeyboardInterrupt:
            print("\n👋 Stopped by user", file=sys.stderr)
            sys.exit(0)

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
