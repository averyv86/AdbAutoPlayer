#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Metrics Cache Manager

LRU cache with TTL (Time-To-Live) for system metrics.

Features:
- TTL-based cache expiration (default: 30 seconds)
- LRU (Least Recently Used) eviction policy
- Persistent cache storage to JSON file
- Cache statistics (hit rate, size, staleness)
- Operations: get, set, invalidate, clear, stats

Usage:
    # Set cache entry
    uv run cache.py --operation set --key cpu --value '{"usage": 45.2}' --ttl 60

    # Get cache entry
    uv run cache.py --operation get --key cpu

    # Get cache statistics
    uv run cache.py --operation stats

    # Clear cache
    uv run cache.py --operation clear

Exit Codes:
    0: Success
    1: Cache miss (for get operation)
    3: Critical error occurred
"""

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click


@dataclass
class CacheEntry:
    """Individual cache entry with TTL."""

    key: str
    value: Any
    timestamp: float
    ttl: int

    def is_expired(self) -> bool:
        """
        Check if cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        return (time.time() - self.timestamp) > self.ttl

    def age_seconds(self) -> float:
        """
        Get age of cache entry in seconds.

        Returns:
            Age in seconds
        """
        return time.time() - self.timestamp


class MetricsCache:
    """LRU cache with TTL for system metrics."""

    def __init__(
        self,
        max_size: int = 50,
        default_ttl: int = 30,
        cache_file: Optional[Path] = None,
    ):
        """
        Initialize metrics cache.

        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
            cache_file: Path to cache persistence file
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache_file = cache_file or (
            Path.home() / ".moai/resource-optimizer/cache/metrics.json"
        )
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if miss/expired
        """
        if key in self.cache:
            entry = self.cache[key]

            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                self.access_order.remove(key)
                self.misses += 1
                return None

            # Update LRU order
            self.access_order.remove(key)
            self.access_order.append(key)
            self.hits += 1
            return entry.value

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl

        # Evict LRU if cache is full and key is new
        if len(self.cache) >= self.max_size and key not in self.cache:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]

        # Add/update entry
        self.cache[key] = CacheEntry(key, value, time.time(), ttl)

        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self.access_order.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        # Calculate staleness statistics
        staleness_data = []
        for entry in self.cache.values():
            age = entry.age_seconds()
            staleness_percent = (age / entry.ttl) * 100
            staleness_data.append(staleness_percent)

        avg_staleness = (
            sum(staleness_data) / len(staleness_data) if staleness_data else 0.0
        )

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization_percent": (len(self.cache) / self.max_size) * 100,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "average_staleness_percent": avg_staleness,
            "default_ttl_seconds": self.default_ttl,
        }

    def save(self) -> None:
        """Persist cache to file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Serialize cache
        serializable_cache = {
            key: {
                "value": entry.value,
                "timestamp": entry.timestamp,
                "ttl": entry.ttl,
            }
            for key, entry in self.cache.items()
        }

        # Add metadata
        data = {
            "metadata": {
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "saved_at": time.time(),
            },
            "cache": serializable_cache,
            "access_order": self.access_order,
            "stats": {
                "hits": self.hits,
                "misses": self.misses,
            },
        }

        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> int:
        """
        Load cache from file.

        Returns:
            Number of entries loaded
        """
        if not self.cache_file.exists():
            return 0

        with open(self.cache_file, "r") as f:
            data = json.load(f)

        # Restore metadata
        metadata = data.get("metadata", {})
        self.max_size = metadata.get("max_size", self.max_size)
        self.default_ttl = metadata.get("default_ttl", self.default_ttl)

        # Restore stats
        stats = data.get("stats", {})
        self.hits = stats.get("hits", 0)
        self.misses = stats.get("misses", 0)

        # Restore cache entries (skip expired ones)
        loaded_count = 0
        for key, entry_data in data.get("cache", {}).items():
            entry = CacheEntry(
                key=key,
                value=entry_data["value"],
                timestamp=entry_data["timestamp"],
                ttl=entry_data["ttl"],
            )

            if not entry.is_expired():
                self.cache[key] = entry
                loaded_count += 1

        # Restore access order (only for non-expired entries)
        self.access_order = [
            key for key in data.get("access_order", []) if key in self.cache
        ]

        return loaded_count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self.cache[key]
            self.access_order.remove(key)

        return len(expired_keys)


@click.command()
@click.option(
    "--operation",
    type=click.Choice(["get", "set", "invalidate", "clear", "stats", "cleanup"]),
    required=True,
    help="Cache operation to perform",
)
@click.option("--key", type=str, help="Cache key (required for get, set, invalidate)")
@click.option("--value", type=str, help="Cache value as JSON string (required for set)")
@click.option(
    "--ttl", type=int, help="Time-to-live in seconds (optional for set, uses default)"
)
@click.option(
    "--cache-file",
    type=click.Path(),
    help="Custom cache file path (default: ~/.moai/resource-optimizer/cache/metrics.json)",
)
def main(
    operation: str,
    key: Optional[str],
    value: Optional[str],
    ttl: Optional[int],
    cache_file: Optional[str],
) -> None:
    """
    Manage metrics cache with TTL and LRU eviction.

    Provides caching operations for system metrics with automatic expiration
    and least-recently-used eviction policy.

    Examples:

        # Set cache entry with 60-second TTL
        uv run cache.py --operation set --key cpu --value '{"usage": 45.2}' --ttl 60

        # Get cache entry
        uv run cache.py --operation get --key cpu

        # Invalidate specific entry
        uv run cache.py --operation invalidate --key cpu

        # Get cache statistics
        uv run cache.py --operation stats

        # Clear all cache
        uv run cache.py --operation clear

        # Cleanup expired entries
        uv run cache.py --operation cleanup
    """
    cache_path = Path(cache_file) if cache_file else None
    cache = MetricsCache(cache_file=cache_path)

    # Load existing cache
    loaded = cache.load()

    try:
        if operation == "get":
            if not key:
                click.echo("❌ --key is required for get operation", err=True)
                sys.exit(3)

            result = cache.get(key)
            if result:
                click.echo(json.dumps(result, indent=2))
                cache.save()  # Save updated stats
                sys.exit(0)
            else:
                click.echo(f"Cache miss for key: {key}")
                cache.save()  # Save updated stats
                sys.exit(1)

        elif operation == "set":
            if not key or not value:
                click.echo(
                    "❌ --key and --value are required for set operation", err=True
                )
                sys.exit(3)

            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError as e:
                click.echo(f"❌ Invalid JSON value: {e}", err=True)
                sys.exit(3)

            cache.set(key, parsed_value, ttl)
            cache.save()
            click.echo(f"✅ Cached: {key} (TTL: {ttl or cache.default_ttl}s)")
            sys.exit(0)

        elif operation == "invalidate":
            if not key:
                click.echo("❌ --key is required for invalidate operation", err=True)
                sys.exit(3)

            removed = cache.invalidate(key)
            cache.save()

            if removed:
                click.echo(f"✅ Invalidated: {key}")
                sys.exit(0)
            else:
                click.echo(f"Key not found: {key}")
                sys.exit(1)

        elif operation == "clear":
            count = cache.clear()
            cache.save()
            click.echo(f"✅ Cache cleared ({count} entries removed)")
            sys.exit(0)

        elif operation == "cleanup":
            removed = cache.cleanup_expired()
            cache.save()
            click.echo(f"✅ Cleanup complete ({removed} expired entries removed)")
            sys.exit(0)

        elif operation == "stats":
            stats = cache.get_stats()
            click.echo(json.dumps(stats, indent=2))
            sys.exit(0)

    except Exception as e:
        click.echo(f"❌ Cache error: {e}", err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
