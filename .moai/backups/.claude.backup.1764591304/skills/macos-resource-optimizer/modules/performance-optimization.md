# Performance Optimization

Parallel execution with asyncio.gather, MetricsCache implementation, lazy loading patterns, and performance benchmarks for achieving 1.5-2.0s target from 2.5s baseline.

## Implementation Status

⚠️ **IMPORTANT**: This document describes **conceptual performance optimization patterns**. The actual implementation uses **UV script parallelization**.

**Current Implementation** (as of 2025-11-30):
- ✅ analyze_all.py with asyncio.gather (parallel execution)
- ✅ cache.py with TTL and LRU eviction
- ✅ Standalone UV scripts (no coordinator.py dependency)
- 🔄 Performance benchmarking in progress (12 scripts)
- 🔄 Target: <2.5s for analyze_all.py parallel execution
- 🔄 Cache hit rate validation pending

**This Document Describes**:
- Conceptual MetricsCache class design
- asyncio.gather parallel execution patterns
- Lazy loading and connection pooling strategies
- Theoretical performance benchmarks

**For Actual Performance Code**: See:
- `.data/scripts/analyze_all.py` (parallel execution)
- `.data/scripts/cache.py` (TTL + LRU cache)

---

## Overview

**Performance Target**: 2.5s → 1.5-2.0s (20-40% improvement)

**Optimization Strategies**:
1. **Parallel Execution**: asyncio.gather for simultaneous analyses
2. **Intelligent Caching**: 30s TTL with LRU eviction
3. **Lazy Loading**: On-demand agent activation
4. **Connection Pooling**: Reuse subprocess connections

## MetricsCache Implementation

### Core Cache Class

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
from collections import OrderedDict

@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    data: Dict[str, Any]
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0

class MetricsCache:
    """
    TTL-based cache with LRU eviction for system metrics

    Features:
    - 30-second TTL (configurable)
    - LRU eviction when at capacity
    - Stale cache support (expired but available)
    - Access tracking for analytics
    """

    def __init__(
        self,
        ttl: int = 30,
        max_size: int = 50,
        stale_threshold: int = 300
    ):
        """
        Initialize cache

        Args:
            ttl: Time-to-live in seconds (default 30)
            max_size: Maximum cache entries (default 50)
            stale_threshold: Threshold for stale cache in seconds (default 300)
        """
        self.ttl = ttl
        self.max_size = max_size
        self.stale_threshold = stale_threshold

        # Use OrderedDict for O(1) LRU operations
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "stale_hits": 0
        }

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached value if not expired

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        entry = self.cache[key]
        current_time = time.time()

        # Check if expired
        if current_time - entry.timestamp > self.ttl:
            self.stats["misses"] += 1
            return None

        # Valid cache hit
        self.stats["hits"] += 1
        entry.access_count += 1
        entry.last_access = current_time

        # Move to end (most recently used)
        self.cache.move_to_end(key)

        return entry.data

    def get_stale(
        self,
        key: str,
        max_age: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve potentially stale cache (expired but recent)

        Useful for fallback when fresh analysis fails.

        Args:
            key: Cache key
            max_age: Maximum age in seconds (default: stale_threshold)

        Returns:
            Stale cached data or None if too old
        """
        if key not in self.cache:
            return None

        entry = self.cache[key]
        current_time = time.time()
        age = current_time - entry.timestamp
        max_age = max_age or self.stale_threshold

        # Check if within stale threshold
        if age <= max_age:
            self.stats["stale_hits"] += 1
            return entry.data

        return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store value with timestamp

        Args:
            key: Cache key
            data: Data to cache
        """
        current_time = time.time()

        # Evict if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        # Create or update entry
        self.cache[key] = CacheEntry(
            data=data,
            timestamp=current_time,
            access_count=1,
            last_access=current_time
        )

        # Move to end (most recently used)
        self.cache.move_to_end(key)

    def _evict_lru(self) -> None:
        """Remove least recently used entry"""
        if not self.cache:
            return

        # Remove first item (least recently used)
        lru_key, _ = self.cache.popitem(last=False)
        self.stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()

    def clear_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries cleared
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = 0.0
        if total_requests > 0:
            hit_rate = self.stats["hits"] / total_requests

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "capacity": self.max_size
        }

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata about cached entry"""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        current_time = time.time()
        age = current_time - entry.timestamp

        return {
            "age_seconds": age,
            "expired": age > self.ttl,
            "stale": age > self.ttl and age <= self.stale_threshold,
            "access_count": entry.access_count,
            "last_access": entry.last_access
        }
```

### Cache Strategy Analysis

**Performance Impact**:

```
Scenario 1: No Cache
├─ Analysis 1: 2.5s (fresh)
├─ Analysis 2: 2.5s (fresh)
├─ Analysis 3: 2.5s (fresh)
└─ Total: 7.5s

Scenario 2: 30s Cache (60% hit rate)
├─ Analysis 1: 2.5s (miss, cached)
├─ Analysis 2: 0.001s (hit)
├─ Analysis 3: 0.001s (hit)
└─ Total: 2.5s (3× faster)

Scenario 3: Stale Cache Fallback
├─ Analysis 1: 2.5s (miss, cached)
├─ Analysis 2: timeout
├─ Fallback: 0.001s (stale hit, 5min old)
└─ Total: 2.5s (degraded but functional)
```

**Cache Hit Rate Optimization**:

```python
def optimize_cache_strategy(usage_pattern: str) -> Dict[str, int]:
    """
    Optimize cache parameters based on usage pattern

    Args:
        usage_pattern: "frequent", "burst", "steady"

    Returns:
        Optimized cache configuration
    """
    strategies = {
        "frequent": {
            "ttl": 60,  # Longer TTL for frequent access
            "max_size": 100,
            "stale_threshold": 600
        },
        "burst": {
            "ttl": 15,  # Shorter TTL for burst workloads
            "max_size": 30,
            "stale_threshold": 120
        },
        "steady": {
            "ttl": 30,  # Balanced TTL
            "max_size": 50,
            "stale_threshold": 300
        }
    }

    return strategies.get(usage_pattern, strategies["steady"])
```

## Parallel Execution with asyncio.gather

### ResourceCoordinator Implementation

```python
import asyncio
from typing import List, Dict, Any, Optional

class ResourceCoordinator:
    """
    Orchestrate parallel resource analysis

    Coordinates 6 category analyses simultaneously using asyncio.gather.
    """

    def __init__(self, wrapper: 'PythonEngineWrapper'):
        """
        Initialize coordinator

        Args:
            wrapper: PythonEngineWrapper instance
        """
        self.wrapper = wrapper
        self.categories = [
            "cpu",
            "memory",
            "disk",
            "network",
            "battery",
            "thermal"
        ]

    async def analyze_all(self) -> Dict[str, Any]:
        """
        Execute all analyses in parallel

        Returns:
            Aggregated results with status and errors
        """
        # Create tasks for all categories
        tasks = [
            self.wrapper.execute_analysis(category)
            for category in self.categories
        ]

        # Execute in parallel with exception handling
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True  # Don't fail on single error
        )

        # Aggregate results
        return self._aggregate_results(results)

    async def analyze_selective(
        self,
        categories: List[str],
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Execute specific category analyses

        Args:
            categories: List of categories to analyze
            parallel: Execute in parallel (True) or sequential (False)

        Returns:
            Aggregated results
        """
        if parallel:
            tasks = [
                self.wrapper.execute_analysis(cat)
                for cat in categories
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for cat in categories:
                try:
                    result = await self.wrapper.execute_analysis(cat)
                    results.append(result)
                except Exception as e:
                    results.append(e)

        return self._aggregate_results(results, categories)

    async def analyze_prioritized(
        self,
        high_priority: List[str],
        low_priority: List[str]
    ) -> Dict[str, Any]:
        """
        Execute analyses with priority levels

        High priority analyses execute first in parallel.
        Low priority analyses execute after in parallel.

        Args:
            high_priority: High priority categories
            low_priority: Low priority categories

        Returns:
            Aggregated results
        """
        # Execute high priority first
        high_tasks = [
            self.wrapper.execute_analysis(cat)
            for cat in high_priority
        ]
        high_results = await asyncio.gather(
            *high_tasks,
            return_exceptions=True
        )

        # Then execute low priority
        low_tasks = [
            self.wrapper.execute_analysis(cat)
            for cat in low_priority
        ]
        low_results = await asyncio.gather(
            *low_tasks,
            return_exceptions=True
        )

        # Combine results
        all_results = high_results + low_results
        all_categories = high_priority + low_priority

        return self._aggregate_results(all_results, all_categories)

    def _aggregate_results(
        self,
        results: List[Any],
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate parallel results

        Args:
            results: List of results or exceptions
            categories: Category names (default: self.categories)

        Returns:
            Aggregated results dictionary
        """
        categories = categories or self.categories
        aggregated = {}
        errors = []
        warnings = []

        for category, result in zip(categories, results):
            if isinstance(result, Exception):
                errors.append({
                    "category": category,
                    "error": str(result),
                    "type": type(result).__name__
                })
            else:
                aggregated[category] = result

                # Check for warnings in result
                if "warnings" in result:
                    warnings.extend([
                        {"category": category, **w}
                        for w in result["warnings"]
                    ])

        # Determine overall status
        status = "success"
        if errors:
            status = "partial" if aggregated else "failed"

        return {
            "status": status,
            "results": aggregated,
            "errors": errors,
            "warnings": warnings,
            "timestamp": time.time(),
            "categories_analyzed": len(aggregated),
            "categories_failed": len(errors)
        }
```

### Performance Benchmarks

```python
import time
from typing import Callable, Any

class PerformanceBenchmark:
    """Benchmark parallel vs sequential execution"""

    def __init__(self, coordinator: ResourceCoordinator):
        self.coordinator = coordinator

    async def benchmark_sequential(
        self,
        categories: List[str]
    ) -> Dict[str, Any]:
        """Benchmark sequential execution"""
        start = time.time()

        results = []
        for category in categories:
            result = await self.coordinator.wrapper.execute_analysis(category)
            results.append(result)

        duration = time.time() - start

        return {
            "mode": "sequential",
            "categories": len(categories),
            "duration": duration,
            "avg_per_category": duration / len(categories)
        }

    async def benchmark_parallel(
        self,
        categories: List[str]
    ) -> Dict[str, Any]:
        """Benchmark parallel execution"""
        start = time.time()

        results = await self.coordinator.analyze_selective(
            categories,
            parallel=True
        )

        duration = time.time() - start

        return {
            "mode": "parallel",
            "categories": len(categories),
            "duration": duration,
            "speedup": self._calculate_speedup(categories, duration)
        }

    def _calculate_speedup(
        self,
        categories: List[str],
        parallel_duration: float
    ) -> float:
        """Calculate speedup from parallel execution"""
        # Assume 2.5s per category sequential
        sequential_duration = len(categories) * 2.5
        return sequential_duration / parallel_duration

    async def run_comparison(
        self,
        categories: List[str]
    ) -> Dict[str, Any]:
        """Run both benchmarks and compare"""
        sequential = await self.benchmark_sequential(categories)
        parallel = await self.benchmark_parallel(categories)

        improvement = (
            (sequential["duration"] - parallel["duration"]) /
            sequential["duration"] * 100
        )

        return {
            "sequential": sequential,
            "parallel": parallel,
            "improvement_percent": improvement
        }
```

## Lazy Loading Patterns

### Agent Activation Strategy

```python
class LazyAgentLoader:
    """Load agents on-demand to reduce memory footprint"""

    def __init__(self):
        self.loaded_agents: Dict[str, Any] = {}
        self.load_times: Dict[str, float] = {}

    def get_agent(self, category: str) -> Any:
        """
        Get agent, loading if necessary

        Args:
            category: Agent category

        Returns:
            Agent instance
        """
        if category not in self.loaded_agents:
            start = time.time()
            self.loaded_agents[category] = self._load_agent(category)
            self.load_times[category] = time.time() - start

        return self.loaded_agents[category]

    def _load_agent(self, category: str) -> Any:
        """Load agent module dynamically"""
        # Lazy import to reduce startup time
        if category == "cpu":
            from .agents import CPUOptimizer
            return CPUOptimizer()
        elif category == "memory":
            from .agents import MemoryOptimizer
            return MemoryOptimizer()
        # ... etc

    def preload_critical(self, categories: List[str]) -> None:
        """Preload critical agents in background"""
        for category in categories:
            self.get_agent(category)

    def unload_unused(self, threshold: float = 300) -> int:
        """
        Unload agents not accessed recently

        Args:
            threshold: Inactivity threshold in seconds

        Returns:
            Number of agents unloaded
        """
        current_time = time.time()
        unloaded = 0

        for category in list(self.loaded_agents.keys()):
            if current_time - self.load_times[category] > threshold:
                del self.loaded_agents[category]
                del self.load_times[category]
                unloaded += 1

        return unloaded
```

## Performance Optimization Techniques

### 1. Connection Pooling

```python
class SubprocessPool:
    """Pool of reusable subprocess connections"""

    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.available: List[subprocess.Popen] = []
        self.in_use: Set[subprocess.Popen] = set()

    async def acquire(self) -> subprocess.Popen:
        """Acquire subprocess from pool"""
        if self.available:
            proc = self.available.pop()
        else:
            proc = await self._create_subprocess()

        self.in_use.add(proc)
        return proc

    async def release(self, proc: subprocess.Popen) -> None:
        """Release subprocess back to pool"""
        self.in_use.remove(proc)

        if len(self.available) < self.pool_size:
            self.available.append(proc)
        else:
            proc.terminate()
            await proc.wait()

    async def _create_subprocess(self) -> subprocess.Popen:
        """Create new subprocess"""
        # Implementation depends on coordinator.py interface
        pass
```

### 2. Batch Processing

```python
class BatchAnalyzer:
    """Process multiple requests in batches"""

    def __init__(
        self,
        coordinator: ResourceCoordinator,
        batch_size: int = 6
    ):
        self.coordinator = coordinator
        self.batch_size = batch_size
        self.queue: List[str] = []

    async def add_request(self, category: str) -> None:
        """Add category to batch queue"""
        self.queue.append(category)

        if len(self.queue) >= self.batch_size:
            await self.process_batch()

    async def process_batch(self) -> Dict[str, Any]:
        """Process all queued requests in parallel"""
        if not self.queue:
            return {}

        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]

        return await self.coordinator.analyze_selective(batch)
```

### 3. Result Streaming

```python
class StreamingAnalyzer:
    """Stream results as they complete"""

    async def analyze_streaming(
        self,
        categories: List[str]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Yield results as they complete

        Args:
            categories: Categories to analyze

        Yields:
            Individual category results
        """
        tasks = {
            asyncio.create_task(
                self.wrapper.execute_analysis(cat)
            ): cat
            for cat in categories
        }

        while tasks:
            done, pending = await asyncio.wait(
                tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                category = tasks.pop(task)
                try:
                    result = await task
                    yield {
                        "category": category,
                        "result": result,
                        "status": "success"
                    }
                except Exception as e:
                    yield {
                        "category": category,
                        "error": str(e),
                        "status": "error"
                    }
```

---

**Status**: ✅ Active (400 lines)
**Last Updated**: 2025-11-29
