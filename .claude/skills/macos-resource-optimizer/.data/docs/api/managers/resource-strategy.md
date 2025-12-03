# manager-resource-strategy API

## Overview

Optimization strategy planner that analyzes metrics from ResourceCoordinator and generates prioritized recommendations with user approval workflow. Translates raw metrics into actionable optimization strategies with Korean language UI support.

**Key Features**:
- Risk-based recommendation prioritization (0-100 scale)
- Korean language user approval workflow
- Multi-level severity assessment
- Rollback capability tracking
- Strategy filtering by risk tolerance

## Classes

### ResourceStrategy

Main strategy planning class.

```python
class ResourceStrategy:
    """Generate and rank optimization strategies from metrics."""

    def __init__(
        self,
        prioritization_model: str = "risk_weighted",
        language: str = "korean"
    ):
        """
        Initialize strategy planner.

        Args:
            prioritization_model: Algorithm for ranking recommendations
                                 Options: "risk_weighted" (default), "simple", "custom"
            language: UI language for approval workflow
                     Options: "korean" (default), "english", "japanese"

        Example:
            >>> strategy = ResourceStrategy(language="korean")
        """
```

### RecommendationEngine

Internal engine for generating recommendations.

```python
class RecommendationEngine:
    """Generate recommendations from metrics using domain rules."""

    def __init__(self, expert_configs: Dict[str, Any]):
        """
        Initialize recommendation engine with expert configurations.

        Args:
            expert_configs: Configuration for each expert optimizer
        """

    def generate_for_category(
        self,
        category: str,
        metrics: Dict
    ) -> List[Recommendation]:
        """Generate recommendations for specific category."""
```

## Methods

### analyze_metrics

Analyze metrics and generate recommendations.

```python
def analyze_metrics(
    self,
    analysis_results: Dict[str, Any],
    include_low_priority: bool = False
) -> List[Recommendation]:
    """
    Analyze coordinator results and generate recommendations.

    Processes metrics from ResourceCoordinator.coordinate_analysis() and
    generates prioritized optimization recommendations. Uses domain rules
    specific to each category.

    Args:
        analysis_results: Output from coordinator.coordinate_analysis()
                         Must include 'categories' key with metrics
        include_low_priority: Include priority < 30 recommendations (default: False)
                             Set True to see all, even low-impact items

    Returns:
        List of Recommendation objects sorted by priority (highest first).
        Each recommendation includes:
        - priority: 0-100 (higher = more urgent)
        - category: Resource type
        - issue: What was detected
        - suggestion: Recommended action
        - risk_level: "low", "medium", "high"
        - rollback_available: Can be reverted

    Raises:
        ValueError: If analysis_results missing required fields
        KeyError: If unexpected metrics structure

    Examples:
        >>> coordinator = ResourceCoordinator()
        >>> analysis = await coordinator.coordinate_analysis()
        >>> strategy = ResourceStrategy()
        >>> recommendations = strategy.analyze_metrics(analysis)
        >>>
        >>> # Show top 5 most urgent
        >>> for rec in recommendations[:5]:
        ...     print(f"{rec.priority:3d} {rec.category:10s} {rec.issue}")
        100 cpu         Critical CPU usage at 96%
         95 thermal     CPU throttling detected
         85 memory      Memory pressure critical
         75 disk        Storage critical (5% free)
         60 network     High latency detected
        >>>
        >>> # Show all including low priority
        >>> all_recs = strategy.analyze_metrics(analysis, include_low_priority=True)
    """
```

### generate_approval_workflow

Generate user approval question set.

```python
def generate_approval_workflow(
    self,
    recommendations: List[Recommendation],
    risk_tolerance: str = "medium",
    max_options: int = 10
) -> Dict[str, Any]:
    """
    Generate Korean AskUserQuestion-compatible workflow.

    Creates a structured user interface for approving optimizations.
    Filters recommendations by risk tolerance and presents in priority order.

    Args:
        recommendations: List from analyze_metrics()
        risk_tolerance: Filter level for which recommendations to show
                       Options: "low" (safe), "medium" (default), "high" (aggressive)
                       - "low": Only risk_level == "low" (< 2% failure rate)
                       - "medium": risk_level in ["low", "medium"] (< 5% failure rate)
                       - "high": All risk_levels (< 20% failure rate)
        max_options: Maximum number of options to present (default: 10)
                    Keeps list manageable for user

    Returns:
        AskUserQuestion-compatible dictionary:
        {
            "questions": [{
                "question": "최적화를 실행하시겠습니까?",  # Korean
                "header": "리소스 최적화",
                "multiSelect": true,
                "options": [
                    {
                        "label": "CPU 사용량 감소",
                        "description": "우선순위 100: CPU 96% 사용 중 - 불필요한 프로세스 종료 (위험: 낮음)"
                    },
                    ...
                ]
            }]
        }

    Raises:
        ValueError: If invalid risk_tolerance
        TypeError: If recommendations not a list

    Examples:
        >>> recommendations = strategy.analyze_metrics(analysis)
        >>>
        >>> # Conservative approach - only safe optimizations
        >>> workflow = strategy.generate_approval_workflow(
        ...     recommendations,
        ...     risk_tolerance="low"
        ... )
        >>>
        >>> # Balanced approach - low and medium risk
        >>> workflow = strategy.generate_approval_workflow(
        ...     recommendations,
        ...     risk_tolerance="medium",
        ...     max_options=8
        ... )
        >>>
        >>> # Aggressive approach - all options
        >>> workflow = strategy.generate_approval_workflow(
        ...     recommendations,
        ...     risk_tolerance="high"
        ... )
    """
```

### apply_recommendations

Apply approved recommendations.

```python
async def apply_recommendations(
    self,
    recommendations: List[Recommendation],
    approved_indices: List[int],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Apply user-approved recommendations.

    Executes optimization for approved recommendations in priority order.

    Args:
        recommendations: Original recommendation list
        approved_indices: Indices of approved items from user selection
        dry_run: If True, show what would happen without executing (default: False)

    Returns:
        {
            "status": "success" | "partial" | "error",
            "applied_count": int,
            "failed_count": int,
            "results": [
                {
                    "recommendation": Recommendation,
                    "status": "success" | "failed",
                    "message": str,
                    "improvement": str,  # e.g., "CPU down from 96% to 45%"
                    "rollback_id": str   # For reverting later
                },
                ...
            ]
        }

    Raises:
        PermissionError: If unable to apply optimization
        TimeoutError: If execution exceeds timeout
        RuntimeError: If critical failure

    Example:
        >>> recommendations = strategy.analyze_metrics(analysis)
        >>> workflow = strategy.generate_approval_workflow(recommendations)
        >>> # User selects indices [0, 2, 4]
        >>> result = await strategy.apply_recommendations(
        ...     recommendations,
        ...     approved_indices=[0, 2, 4]
        ... )
        >>> print(f"Applied: {result['applied_count']}/{len([0,2,4])}")
    """
```

### get_risk_assessment

Get detailed risk assessment for recommendation.

```python
def get_risk_assessment(
    self,
    recommendation: Recommendation
) -> Dict[str, Any]:
    """
    Get detailed risk analysis for specific recommendation.

    Args:
        recommendation: Recommendation object to assess

    Returns:
        {
            "risk_level": "low" | "medium" | "high",
            "failure_probability": float,  # 0.0-1.0
            "impact_if_fails": str,
            "mitigation_steps": [str, ...],
            "similar_past_results": [
                {
                    "success_rate": float,
                    "improvement_range": str,
                    "sample_size": int
                },
                ...
            ]
        }

    Example:
        >>> rec = recommendations[0]
        >>> risk = strategy.get_risk_assessment(rec)
        >>> print(f"Failure probability: {risk['failure_probability']*100:.1f}%")
    """
```

### get_improvement_projection

Project expected improvements.

```python
def get_improvement_projection(
    self,
    recommendations: List[Recommendation],
    current_metrics: Dict
) -> Dict[str, Any]:
    """
    Project expected improvements from recommendations.

    Args:
        recommendations: List of recommendations to apply
        current_metrics: Current metrics from coordinator

    Returns:
        {
            "projected_metrics": {
                "cpu_percent": float,
                "memory_percent": float,
                ...
            },
            "improvement_confidence": float,  # 0.0-1.0
            "time_to_effect": str,  # "immediate", "5-10 minutes", "1 hour"
            "expected_benefits": [str, ...]
        }

    Example:
        >>> projections = strategy.get_improvement_projection(
        ...     recommendations,
        ...     analysis['categories']
        ... )
        >>> print(f"Projected CPU: {projections['projected_metrics']['cpu_percent']}%")
    """
```

## Data Structures

### Recommendation

```python
@dataclass
class Recommendation:
    """Single optimization recommendation."""
    category: str              # "cpu", "memory", "disk", "network", "battery", "thermal"
    priority: int              # 0-100 (higher = more urgent)
    issue: str                 # e.g., "Critical CPU usage at 96%"
    suggestion: str            # e.g., "Terminate Firefox (2.1 GB memory, 45% CPU)"
    expected_improvement: str  # e.g., "CPU: 96% → 50%, Memory: 8.2 GB → 6.8 GB"
    risk_level: str           # "low", "medium", "high"
    impact_description: str   # "Immediate reduction in heat generation"
    rollback_available: bool  # Can be reverted
    timestamp: datetime
    optimization_type: OptimizationType
```

### OptimizationType

```python
class OptimizationType(Enum):
    """Type of optimization action."""
    KILL_PROCESS = "kill_process"           # Terminate process
    REDUCE_USAGE = "reduce_usage"           # Throttle process
    CLEANUP = "cleanup"                     # Clear caches, temp files
    TUNE_SETTING = "tune_setting"           # Adjust system settings
    DISABLE_FEATURE = "disable_feature"     # Disable feature
```

### RiskLevel

```python
class RiskLevel(Enum):
    """Risk assessment for optimization."""
    LOW = "low"          # < 2% failure rate
    MEDIUM = "medium"    # 2-5% failure rate
    HIGH = "high"        # 5-20% failure rate
```

### StrategyConfig

```python
@dataclass
class StrategyConfig:
    """Configuration for strategy planner."""
    prioritization_model: str = "risk_weighted"
    language: str = "korean"
    default_risk_tolerance: str = "medium"
    max_recommendations: int = 20
    confidence_threshold: float = 0.75
```

## Usage Examples

### Example 1: Complete Workflow

```python
import asyncio
from manager_resource_coordinator import ResourceCoordinator
from manager_resource_strategy import ResourceStrategy

async def optimize_system():
    # Step 1: Analyze
    coordinator = ResourceCoordinator()
    analysis = await coordinator.coordinate_analysis()

    # Step 2: Generate strategy
    strategy = ResourceStrategy(language="korean")
    recommendations = strategy.analyze_metrics(analysis)

    # Step 3: Show user options
    workflow = strategy.generate_approval_workflow(
        recommendations,
        risk_tolerance="medium"
    )
    print(f"Found {len(recommendations)} optimization opportunities")
    print(f"Top priority: {recommendations[0].issue}")

    # Step 4: Apply approved (mock here)
    approved_indices = [0, 2]  # User selected these
    result = await strategy.apply_recommendations(
        recommendations,
        approved_indices=approved_indices
    )

    print(f"Applied {result['applied_count']} optimizations")

asyncio.run(optimize_system())
```

### Example 2: Risk-Based Filtering

```python
# Conservative - only safe optimizations
safe_only = strategy.generate_approval_workflow(
    recommendations,
    risk_tolerance="low"
)

# Balanced
balanced = strategy.generate_approval_workflow(
    recommendations,
    risk_tolerance="medium"
)

# Aggressive
aggressive = strategy.generate_approval_workflow(
    recommendations,
    risk_tolerance="high"
)
```

### Example 3: Risk Assessment

```python
# Get top recommendation
top_rec = recommendations[0]

# Assess risks
risk = strategy.get_risk_assessment(top_rec)

print(f"Risk level: {risk['risk_level']}")
print(f"Failure probability: {risk['failure_probability']*100:.1f}%")
print(f"Mitigation steps:")
for step in risk['mitigation_steps']:
    print(f"  - {step}")
```

### Example 4: Improvement Projection

```python
# Project improvements from top 3 recommendations
projections = strategy.get_improvement_projection(
    recommendations[:3],
    analysis['categories']
)

print("Projected improvements:")
for metric, value in projections['projected_metrics'].items():
    print(f"  {metric}: {value}")

print(f"\nTime to effect: {projections['time_to_effect']}")
print(f"Confidence: {projections['improvement_confidence']*100:.0f}%")
```

### Example 5: Dry Run Mode

```python
# Test what would happen without executing
result = await strategy.apply_recommendations(
    recommendations,
    approved_indices=[0, 1],
    dry_run=True
)

print("Dry run results:")
for item in result['results']:
    print(f"  {item['recommendation'].issue}: {item['status']}")

# If looks good, apply for real
result = await strategy.apply_recommendations(
    recommendations,
    approved_indices=[0, 1],
    dry_run=False
)
```

## Priority Calculation

Recommendations are prioritized using:

```
Priority = (50 * urgency_factor) +
           (30 * impact_factor) +
           (20 * confidence_factor) -
           (risk_penalty)

Where:
  urgency_factor: 0-100 based on current metric severity
  impact_factor: Expected improvement magnitude
  confidence_factor: Historical success rate
  risk_penalty: 0-50 based on failure probability
```

Examples:
- **Priority 100**: Critical CPU at 96% + high confidence + low risk
- **Priority 75**: High memory usage + medium confidence + medium risk
- **Priority 30**: Minor disk space + low impact + high risk

## Language Support

UI strings are auto-translated:

```python
# Korean (기본값)
strategy = ResourceStrategy(language="korean")

# English
strategy = ResourceStrategy(language="english")

# Japanese
strategy = ResourceStrategy(language="japanese")
```

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()
strategy = ResourceStrategy()

# Full pipeline
metrics = await coordinator.coordinate_analysis()
recommendations = strategy.analyze_metrics(metrics)
workflow = strategy.generate_approval_workflow(recommendations)
# Present workflow to user...
result = await strategy.apply_recommendations(
    recommendations,
    approved_indices=user_selection
)
```

## Rollback System

Each applied recommendation is tracked for rollback:

```python
# Apply recommendations
result = await strategy.apply_recommendations(recommendations, [0, 1])

# Later, rollback if needed
for applied in result['results']:
    if applied['status'] == 'success':
        await strategy.rollback(applied['rollback_id'])
```

## Thread Safety

ResourceStrategy is **thread-safe** for read operations but not for writes. For concurrent access:

```python
from threading import Lock

strategy = ResourceStrategy()
lock = Lock()

def safe_analyze(metrics):
    with lock:
        return strategy.analyze_metrics(metrics)
```

## Monitoring & Logging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Strategy will log all decisions
strategy = ResourceStrategy()
recommendations = strategy.analyze_metrics(analysis)
# Logs will show: priority calculation, risk assessment, etc.
```

## Performance Characteristics

| Operation | Time |
|-----------|------|
| analyze_metrics() | 0.2-0.3s |
| generate_approval_workflow() | 0.1-0.2s |
| get_risk_assessment() | 0.05-0.1s |
| apply_recommendations() | 1-30s (depends on actions) |

## API Stability

This API is **stable** as of version 1.0.0.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-30 | Initial release |

---

**Status**: Production Ready
**Last Updated**: 2025-11-30
**Maintainer**: MoAI Development Team
