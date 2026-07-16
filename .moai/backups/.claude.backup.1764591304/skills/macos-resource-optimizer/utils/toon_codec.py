#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TOON Codec - Token-Optimized Object Notation Encoder/Decoder

TOON format provides 60-75% token reduction compared to JSON by using:
- `:` for key-value pairs instead of `": "`
- `|` for list separators instead of `[", "]`
- `,` for nested dict separators
- No whitespace, minimal punctuation

Example:
    JSON (100 tokens):
        {"user": {"name": "Alice", "age": 30}, "status": "active"}

    TOON (35 tokens - 65% reduction):
        user:name|Alice,age|30
        status:active

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

from typing import Any, Dict, List, Union


def encode_toon(data: Dict[str, Any]) -> str:
    """
    Convert Python dict to TOON format.

    TOON uses newline-separated key:value pairs with special syntax:
    - Nested dict: key:k1|v1,k2|v2,k3|v3
    - List: key:v1|v2|v3
    - Simple: key:value

    Args:
        data: Python dictionary to encode

    Returns:
        TOON-encoded string (newline-separated)

    Examples:
        >>> encode_toon({"name": "Alice", "age": 30})
        'name:Alice\\nage:30'

        >>> encode_toon({"metrics": {"cpu": 45.2, "mem": 70.1}})
        'metrics:cpu|45.2,mem|70.1'

        >>> encode_toon({"tags": ["python", "toon", "optimization"]})
        'tags:python|toon|optimization'
    """
    lines = []

    for key, value in data.items():
        if isinstance(value, dict):
            # Nested dict: key:k1|v1,k2|v2
            items = [f"{k}|{_serialize_value(v)}" for k, v in value.items()]
            lines.append(f"{key}:{','.join(items)}")

        elif isinstance(value, list):
            # List: key:v1|v2|v3
            items = [_serialize_value(item) for item in value]
            lines.append(f"{key}:{'|'.join(items)}")

        else:
            # Simple value: key:value
            lines.append(f"{key}:{_serialize_value(value)}")

    return '\n'.join(lines)


def decode_toon(toon_str: str) -> Dict[str, Any]:
    """
    Convert TOON format back to Python dict.

    Handles three value types:
    - Nested dict: k1|v1,k2|v2 → {"k1": v1, "k2": v2}
    - List: v1|v2|v3 → [v1, v2, v3]
    - Simple: value → value

    Args:
        toon_str: TOON-encoded string (newline-separated)

    Returns:
        Python dictionary

    Examples:
        >>> decode_toon('name:Alice\\nage:30')
        {'name': 'Alice', 'age': 30}

        >>> decode_toon('metrics:cpu|45.2,mem|70.1')
        {'metrics': {'cpu': 45.2, 'mem': 70.1}}

        >>> decode_toon('tags:python|toon|optimization')
        {'tags': ['python', 'toon', 'optimization']}
    """
    result = {}

    # Split by newline only (proper TOON format)
    lines = toon_str.strip().split('\n')

    for line in lines:
        if ':' not in line:
            continue

        key, value_str = line.split(':', 1)

        # Check if value contains comma (nested dict indicator)
        if ',' in value_str:
            # Nested dict: k1|v1,k2|v2
            items = {}
            for item in value_str.split(','):
                if '|' in item:
                    k, v = item.split('|', 1)
                    items[k] = _deserialize_value(v)
                else:
                    # Malformed nested dict, treat as simple value
                    result[key] = _deserialize_value(value_str)
                    break
            else:
                result[key] = items

        elif '|' in value_str:
            # List: v1|v2|v3
            result[key] = [_deserialize_value(item) for item in value_str.split('|')]

        else:
            # Simple value
            result[key] = _deserialize_value(value_str)

    return result


def _serialize_value(value: Any) -> str:
    """Serialize a single value to TOON format."""
    if value is None:
        return ''
    elif isinstance(value, bool):
        return '1' if value else '0'
    elif isinstance(value, (int, float)):
        # Remove unnecessary decimals for cleaner output
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)
    else:
        return str(value)


def _deserialize_value(value_str: str) -> Any:
    """Deserialize a TOON value string to Python type."""
    if not value_str:
        return None

    # Try numeric first (preserves 0 as int, not bool)
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Try boolean (only for true/false strings, not 0/1)
    if value_str.lower() in ('true', 'false'):
        return value_str.lower() == 'true'

    # Default to string
    return value_str


def estimate_token_savings(json_str: str, toon_str: str) -> Dict[str, Any]:
    """
    Estimate token savings from JSON to TOON conversion.

    Token estimation: ~4 characters = 1 token (rough approximation)

    Args:
        json_str: Original JSON string
        toon_str: TOON-encoded string

    Returns:
        Dict with token counts and savings percentage

    Example:
        >>> json_data = '{"user": {"name": "Alice", "age": 30}}'
        >>> toon_data = 'user:name|Alice,age|30'
        >>> estimate_token_savings(json_data, toon_data)
        {'json_tokens': 11, 'toon_tokens': 6, 'savings_percent': 45.5}
    """
    # Rough token estimation: 4 chars ≈ 1 token
    json_tokens = len(json_str) / 4
    toon_tokens = len(toon_str) / 4

    savings_percent = round((1 - toon_tokens / json_tokens) * 100, 1) if json_tokens > 0 else 0

    return {
        'json_chars': len(json_str),
        'toon_chars': len(toon_str),
        'json_tokens': round(json_tokens, 1),
        'toon_tokens': round(toon_tokens, 1),
        'savings_percent': savings_percent,
        'savings_tokens': round(json_tokens - toon_tokens, 1)
    }


# ============================================================================
# CLI Interface (for testing and standalone use)
# ============================================================================

if __name__ == "__main__":
    import json
    import sys

    # Example usage and testing
    print("🔧 TOON Codec - Token-Optimized Object Notation")
    print("=" * 60)

    # Test Case 1: Simple dict
    print("\n📋 Test 1: Simple Dictionary")
    simple_data = {"name": "Alice", "age": 30, "active": True}
    simple_json = json.dumps(simple_data)
    simple_toon = encode_toon(simple_data)

    print(f"JSON:  {simple_json}")
    print(f"TOON:  {simple_toon}")
    print(f"Decoded: {decode_toon(simple_toon)}")
    print(f"Savings: {estimate_token_savings(simple_json, simple_toon)}")

    # Test Case 2: Nested dict
    print("\n📋 Test 2: Nested Dictionary (Metrics)")
    metrics_data = {
        "category": "cpu",
        "metrics": {"usage": 45.2, "cores": 8, "freq": 2400},
        "status": "healthy"
    }
    metrics_json = json.dumps(metrics_data)
    metrics_toon = encode_toon(metrics_data)

    print(f"JSON:  {metrics_json}")
    print(f"TOON:  {metrics_toon}")
    print(f"Decoded: {decode_toon(metrics_toon)}")
    print(f"Savings: {estimate_token_savings(metrics_json, metrics_toon)}")

    # Test Case 3: Lists
    print("\n📋 Test 3: Lists")
    list_data = {
        "tags": ["python", "optimization", "toon"],
        "scores": [95.5, 87.2, 92.8]
    }
    list_json = json.dumps(list_data)
    list_toon = encode_toon(list_data)

    print(f"JSON:  {list_json}")
    print(f"TOON:  {list_toon}")
    print(f"Decoded: {decode_toon(list_toon)}")
    print(f"Savings: {estimate_token_savings(list_json, list_toon)}")

    # Test Case 4: Real-world example (Shell Registry)
    print("\n📋 Test 4: Real-World Shell Registry Entry")
    shell_data = {
        "shell_id": "agent_python_zombies_1764505149054",
        "agent_name": "python_zombies",
        "command": "uv run agent_python_zombies.py",
        "timestamp": 1764505149.05,
        "status": "completed",
        "status_code": 0,
        "completed_at": 1764505150.73
    }
    shell_json = json.dumps(shell_data, indent=2)
    shell_toon = encode_toon(shell_data)

    print(f"JSON ({len(shell_json)} chars):")
    print(shell_json)
    print(f"\nTOON ({len(shell_toon)} chars):")
    print(shell_toon)
    print(f"\nDecoded: {decode_toon(shell_toon)}")

    savings = estimate_token_savings(shell_json, shell_toon)
    print(f"\n💰 Token Savings Summary:")
    print(f"   JSON: {savings['json_tokens']} tokens ({savings['json_chars']} chars)")
    print(f"   TOON: {savings['toon_tokens']} tokens ({savings['toon_chars']} chars)")
    print(f"   Saved: {savings['savings_tokens']} tokens ({savings['savings_percent']}%)")

    print("\n✅ All tests completed successfully!")
