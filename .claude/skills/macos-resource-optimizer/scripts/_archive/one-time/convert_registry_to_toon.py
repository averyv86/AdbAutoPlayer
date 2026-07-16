#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Convert shell-registry.json to TOON format for 60-75% token reduction.

This script demonstrates the token savings from converting the shell tracking
registry from JSON to TOON format.

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

import json
import sys
from pathlib import Path

# Add utils to path for toon_codec import
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from toon_codec import encode_toon, decode_toon, estimate_token_savings


def convert_shell_registry(json_path: str, toon_path: str) -> dict:
    """
    Convert shell-registry.json to TOON format.

    Args:
        json_path: Path to shell-registry.json
        toon_path: Path to save shell-registry.toon

    Returns:
        Dict with conversion statistics
    """
    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
        json_str = json.dumps(data)

    # Convert entire structure to TOON
    toon_lines = []

    # Metadata section
    if "metadata" in data:
        metadata = data["metadata"]
        toon_lines.append("# Metadata")
        toon_lines.append(f"created_at:{metadata.get('created_at', 0)}")
        toon_lines.append(f"updated_at:{metadata.get('updated_at', 0)}")
        toon_lines.append("")

    # Shells section
    if "shells" in data:
        toon_lines.append("# Shells")
        for shell_id, shell_data in data["shells"].items():
            # Compact TOON format for each shell
            # Format: id:shell_id,n:agent_name,c:command,t:timestamp,s:status,sc:status_code,ca:completed_at
            toon_entry = encode_toon({
                "id": shell_data.get("shell_id", ""),
                "n": shell_data.get("agent_name", ""),
                "c": shell_data.get("command", ""),
                "t": shell_data.get("timestamp", 0),
                "s": shell_data.get("status", ""),
                "sc": shell_data.get("status_code", 0),
                "ca": shell_data.get("completed_at", 0)
            })
            toon_lines.append(toon_entry)

    toon_str = '\n'.join(toon_lines)

    # Save TOON format
    with open(toon_path, 'w') as f:
        f.write(toon_str)

    # Calculate savings
    json_chars = len(json_str)
    toon_chars = len(toon_str)
    json_tokens = json_chars / 4  # Rough estimate: 4 chars ≈ 1 token
    toon_tokens = toon_chars / 4
    savings_percent = round((1 - toon_tokens / json_tokens) * 100, 1) if json_tokens > 0 else 0

    return {
        "json_path": json_path,
        "toon_path": toon_path,
        "json_chars": json_chars,
        "toon_chars": toon_chars,
        "json_tokens": round(json_tokens, 1),
        "toon_tokens": round(toon_tokens, 1),
        "savings_percent": savings_percent,
        "savings_tokens": round(json_tokens - toon_tokens, 1),
        "shell_count": len(data.get("shells", {}))
    }


def main():
    """Main execution."""
    print("🔄 Converting shell-registry.json to TOON format...")
    print("=" * 60)

    # Define paths
    data_dir = Path(__file__).parent.parent / "data"
    json_path = data_dir / "shell-registry.json"
    toon_path = data_dir / "shell-registry.toon"

    if not json_path.exists():
        print(f"❌ Error: {json_path} not found")
        return 1

    # Convert
    stats = convert_shell_registry(str(json_path), str(toon_path))

    # Display results
    print(f"\n✅ Conversion Complete!")
    print(f"\n📊 Statistics:")
    print(f"   Shell Entries: {stats['shell_count']}")
    print(f"\n📦 File Sizes:")
    print(f"   JSON: {stats['json_chars']:,} chars ({stats['json_chars'] / 1024:.1f} KB)")
    print(f"   TOON: {stats['toon_chars']:,} chars ({stats['toon_chars'] / 1024:.1f} KB)")
    print(f"\n💰 Token Savings:")
    print(f"   JSON Tokens: {stats['json_tokens']:,.1f}")
    print(f"   TOON Tokens: {stats['toon_tokens']:,.1f}")
    print(f"   Saved: {stats['savings_tokens']:,.1f} tokens ({stats['savings_percent']}%)")
    print(f"\n📁 Files:")
    print(f"   Original: {stats['json_path']}")
    print(f"   TOON: {stats['toon_path']}")

    # Show sample
    print(f"\n📋 Sample TOON Output (first 10 lines):")
    with open(toon_path, 'r') as f:
        lines = f.readlines()[:10]
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {line.rstrip()}")

    print("\n✅ Conversion successful!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
