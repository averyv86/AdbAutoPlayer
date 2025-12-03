# optimize.py Algorithm Design

**Purpose**: Transform analysis results into actionable, prioritized optimization recommendations with risk assessment and user approval workflow.

**Target Implementation**: Phase 2 Day 4 (2025-12-01)

**Version**: 1.0.0

---

## 1. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: analyze_all.py JSON                   │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   "timestamp": "2025-11-30T...",                               │
│   "categories": {                                               │
│     "cpu": { "metrics": {...}, "analysis": {...} },           │
│     "memory": { "metrics": {...}, "analysis": {...} },        │
│     "disk": { "metrics": {...}, "analysis": {...} },          │
│     "network": { "metrics": {...}, "analysis": {...} },       │
│     "battery": { "metrics": {...}, "analysis": {...} },       │
│     "thermal": { "metrics": {...}, "analysis": {...} }        │
│   },                                                            │
│   "overall": {                                                  │
│     "status": "warning|critical|healthy",                      │
│     "risk_level": "low|medium|high|critical",                  │
│     "health_score": 75.5                                       │
│   }                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: Parse & Extract Issues                    │
├─────────────────────────────────────────────────────────────────┤
│ • Load JSON from stdin or file                                  │
│ • Validate structure and data integrity                         │
│ • Extract per-category issues from recommendations              │
│ • Extract current state metrics                                 │
│ • Identify actionable items vs informational                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 2: Generate Optimization Strategies               │
├─────────────────────────────────────────────────────────────────┤
│ • CPU: Process priority, affinity, thermal throttling           │
│ • Memory: Swap config, compression, process limits              │
│ • Disk: I/O scheduling, cache tuning, TRIM                      │
│ • Network: TCP tuning, connection pooling, DNS cache            │
│ • Battery: Power mode, display brightness, background apps      │
│ • Thermal: Fan control, throttling thresholds, scheduling       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 3: Prioritize & Risk Assessment                │
├─────────────────────────────────────────────────────────────────┤
│ • Calculate priority scores (impact × urgency / risk)           │
│ • Assess rollback feasibility                                   │
│ • Group by category and severity                                │
│ • Sort by priority score (highest first)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 4: User Approval Workflow (Korean)           │
├─────────────────────────────────────────────────────────────────┤
│ • Present top N recommendations (default: 5)                    │
│ • Show category, issue, actions, impact, risk                   │
│ • Request user selection via AskUserQuestion                    │
│ • Allow: "전체 실행", "선택 실행", "건너뛰기"                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 5: Execution (Dry-run or Apply Mode)             │
├─────────────────────────────────────────────────────────────────┤
│ DRY-RUN MODE (default):                                         │
│ • Simulate all optimizations                                    │
│ • Show expected changes                                         │
│ • Generate preview report                                       │
│                                                                 │
│ APPLY MODE (--apply flag):                                      │
│ • Backup current settings to .data/backups/                     │
│ • Execute optimizations sequentially                            │
│ • Verify each step (success/failure)                            │
│ • Auto-rollback on critical error                               │
│ • Log all actions to .data/logs/optimization-{timestamp}.log    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT: Optimization Report                    │
├─────────────────────────────────────────────────────────────────┤
│ JSON: Detailed results with metrics                             │
│ Human-readable: Summary with next steps                         │
│ Exit code: 0 (success), 1 (partial), 2 (failed), 3 (error)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Classes & Data Models

### 2.1 Optimization Data Model

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class OptimizationAction:
    """Single optimization action (e.g., adjust a setting)"""
    command: str              # Shell command to execute
    description: str          # Human-readable description
    requires_sudo: bool       # Whether sudo is needed
    reversible: bool          # Whether action can be undone
    rollback_command: Optional[str] = None  # Command to reverse
    verification_command: Optional[str] = None  # Check if applied


@dataclass
class Optimization:
    """Complete optimization recommendation"""
    # Identification
    id: str                   # opt-001, opt-002, etc.
    category: str             # cpu, memory, disk, network, battery, thermal

    # Issue description
    issue: str                # Problem detected
    current_state: Dict       # Current metric values
    target_state: Dict        # Expected after optimization

    # Actions
    actions: List[OptimizationAction]  # List of steps to execute

    # Impact & Risk
    impact: str               # "low", "medium", "high"
    risk: str                 # "low", "medium", "high"
    urgency: str              # "low", "medium", "high", "critical"

    # Priority calculation
    priority_score: float     # 0.0-10.0 (higher = more important)

    # Rollback support
    rollback_supported: bool  # Can we undo this?
    backup_needed: bool       # Backup files before execution?
    backup_paths: List[str] = field(default_factory=list)

    # Expected improvements
    estimated_improvement: str  # "15-20% CPU reduction"

    # Execution tracking
    applied: bool = False
    execution_time: Optional[datetime] = None
    execution_result: Optional[str] = None  # "success", "failed", "partial"


@dataclass
class RiskAssessment:
    """Risk assessment for optimization plan"""
    overall_risk: str         # "low", "medium", "high", "critical"
    blocked_optimizations: List[str]  # IDs of blocked items (too risky)
    warnings: List[str]       # Warning messages
    requires_backup: bool     # Any optimization needs backup?
    requires_sudo: bool       # Any action needs sudo?
    reversibility_score: float  # % of actions that can be reversed


@dataclass
class ExecutionPlan:
    """Complete execution plan with all optimizations"""
    optimizations: List[Optimization]
    total_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    risk_assessment: RiskAssessment
    estimated_duration: str   # "5-10 minutes"
    backup_directory: Optional[str] = None
```

---

### 2.2 OptimizationEngine Class

```python
class OptimizationEngine:
    """Core optimization recommendation engine"""

    def __init__(self, analysis_data: Dict, verbose: bool = False):
        """
        Initialize optimization engine with analysis results.

        Args:
            analysis_data: Output from analyze_all.py (JSON dict)
            verbose: Enable verbose logging
        """
        self.analysis = analysis_data
        self.verbose = verbose
        self.optimizations: List[Optimization] = []
        self.risk_assessment: Optional[RiskAssessment] = None

    def load_analysis_results(self) -> Dict:
        """
        Parse and validate analysis results.

        Returns:
            Structured analysis data with categories

        Raises:
            ValueError: If analysis data is invalid or incomplete
        """
        required_keys = ["timestamp", "categories", "overall"]
        for key in required_keys:
            if key not in self.analysis:
                raise ValueError(f"Missing required key: {key}")

        # Validate each category
        expected_categories = ["cpu", "memory", "disk", "network", "battery", "thermal"]
        categories = self.analysis.get("categories", {})

        for cat in expected_categories:
            if cat not in categories:
                self._log(f"Warning: Missing category {cat}")

        return self.analysis

    def generate_optimizations(self) -> List[Optimization]:
        """
        Generate optimization recommendations from analysis.

        Returns:
            List of Optimization objects
        """
        optimizations = []
        opt_id_counter = 1

        for category, data in self.analysis["categories"].items():
            analysis = data.get("analysis", {})
            metrics = data.get("metrics", {})
            recommendations = analysis.get("recommendations", [])

            # Convert each recommendation to Optimization
            for rec in recommendations:
                opt = self._create_optimization(
                    opt_id=f"opt-{opt_id_counter:03d}",
                    category=category,
                    recommendation=rec,
                    metrics=metrics,
                    analysis=analysis
                )
                if opt:
                    optimizations.append(opt)
                    opt_id_counter += 1

        self.optimizations = optimizations
        return optimizations

    def prioritize_recommendations(self) -> List[Optimization]:
        """
        Sort optimizations by priority score (highest first).

        Returns:
            Sorted list of optimizations
        """
        # Calculate priority scores
        for opt in self.optimizations:
            opt.priority_score = self._calculate_priority_score(opt)

        # Sort by priority (descending)
        sorted_opts = sorted(
            self.optimizations,
            key=lambda x: x.priority_score,
            reverse=True
        )

        return sorted_opts

    def assess_risks(self) -> RiskAssessment:
        """
        Assess overall risk of execution plan.

        Returns:
            RiskAssessment object
        """
        blocked = []
        warnings = []
        requires_backup = False
        requires_sudo = False
        reversible_count = 0

        for opt in self.optimizations:
            # Block critical risk without rollback
            if opt.risk == "high" and not opt.rollback_supported:
                blocked.append(opt.id)
                warnings.append(
                    f"{opt.id}: High risk, no rollback - BLOCKED"
                )

            # Check backup needs
            if opt.backup_needed:
                requires_backup = True

            # Check sudo requirements
            if any(action.requires_sudo for action in opt.actions):
                requires_sudo = True

            # Count reversible actions
            if opt.rollback_supported:
                reversible_count += 1

        # Calculate reversibility score
        total = len(self.optimizations)
        reversibility_score = (reversible_count / total * 100) if total > 0 else 0.0

        # Determine overall risk
        risk_levels = [opt.risk for opt in self.optimizations if opt.id not in blocked]
        if any(r == "high" for r in risk_levels):
            overall_risk = "high"
        elif any(r == "medium" for r in risk_levels):
            overall_risk = "medium"
        else:
            overall_risk = "low"

        self.risk_assessment = RiskAssessment(
            overall_risk=overall_risk,
            blocked_optimizations=blocked,
            warnings=warnings,
            requires_backup=requires_backup,
            requires_sudo=requires_sudo,
            reversibility_score=round(reversibility_score, 1)
        )

        return self.risk_assessment

    def create_execution_plan(self) -> ExecutionPlan:
        """
        Create complete execution plan.

        Returns:
            ExecutionPlan with all optimizations and metadata
        """
        # Ensure optimizations are prioritized
        sorted_opts = self.prioritize_recommendations()

        # Ensure risk assessment is done
        if not self.risk_assessment:
            self.assess_risks()

        # Count by priority
        high = sum(1 for o in sorted_opts if o.impact == "high")
        medium = sum(1 for o in sorted_opts if o.impact == "medium")
        low = sum(1 for o in sorted_opts if o.impact == "low")

        # Estimate duration (2 min per optimization)
        total = len(sorted_opts)
        est_minutes = total * 2
        if est_minutes < 5:
            estimated_duration = "< 5 minutes"
        elif est_minutes < 10:
            estimated_duration = "5-10 minutes"
        elif est_minutes < 30:
            estimated_duration = "10-30 minutes"
        else:
            estimated_duration = f"{est_minutes} minutes"

        # Create backup directory path
        backup_dir = None
        if self.risk_assessment.requires_backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f".data/backups/optimization-{timestamp}"

        return ExecutionPlan(
            optimizations=sorted_opts,
            total_count=total,
            high_priority_count=high,
            medium_priority_count=medium,
            low_priority_count=low,
            risk_assessment=self.risk_assessment,
            estimated_duration=estimated_duration,
            backup_directory=backup_dir
        )

    def _calculate_priority_score(self, opt: Optimization) -> float:
        """
        Calculate priority score for optimization.

        Formula:
        Priority = (Impact × 0.4) + (Risk_Inverted × 0.3) + (Urgency × 0.3)

        Scores:
        - Impact: high=3, medium=2, low=1
        - Risk (inverted): low=3, medium=2, high=1
        - Urgency: critical=4, high=3, medium=2, low=1

        Returns:
            Priority score (0.0-10.0)
        """
        # Impact score
        impact_scores = {"high": 3, "medium": 2, "low": 1}
        impact = impact_scores.get(opt.impact, 1)

        # Risk score (inverted - prefer low risk)
        risk_scores = {"low": 3, "medium": 2, "high": 1}
        risk = risk_scores.get(opt.risk, 1)

        # Urgency score
        urgency_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        urgency = urgency_scores.get(opt.urgency, 1)

        # Weighted calculation
        score = (impact * 0.4) + (risk * 0.3) + (urgency * 0.3)

        # Normalize to 0-10 scale
        normalized = (score / 3.4) * 10

        return round(normalized, 2)

    def _create_optimization(
        self,
        opt_id: str,
        category: str,
        recommendation: Dict,
        metrics: Dict,
        analysis: Dict
    ) -> Optional[Optimization]:
        """
        Create Optimization object from recommendation.

        Args:
            opt_id: Unique optimization ID
            category: Category name
            recommendation: Single recommendation dict
            metrics: Category metrics
            analysis: Category analysis results

        Returns:
            Optimization object or None if not actionable
        """
        # Extract recommendation data
        if isinstance(recommendation, dict):
            issue = recommendation.get("issue", recommendation.get("action", "Unknown"))
            action_desc = recommendation.get("action", issue)
        else:
            issue = str(recommendation)
            action_desc = issue

        # Determine if actionable
        if not self._is_actionable(issue):
            return None

        # Generate actions based on category and issue
        actions = self._generate_actions(category, issue, metrics)
        if not actions:
            return None

        # Determine impact, risk, urgency
        impact = self._assess_impact(category, issue, metrics)
        risk = self._assess_risk(category, issue)
        urgency = self._assess_urgency(analysis.get("status"), metrics)

        # Check rollback support
        rollback_supported = all(a.reversible for a in actions)

        # Determine backup needs
        backup_needed = risk in ["medium", "high"]
        backup_paths = self._get_backup_paths(category, actions)

        # Generate improvement estimate
        improvement = self._estimate_improvement(category, issue, metrics)

        return Optimization(
            id=opt_id,
            category=category,
            issue=issue,
            current_state=self._extract_current_state(metrics),
            target_state=self._calculate_target_state(category, metrics),
            actions=actions,
            impact=impact,
            risk=risk,
            urgency=urgency,
            priority_score=0.0,  # Calculated later
            rollback_supported=rollback_supported,
            backup_needed=backup_needed,
            backup_paths=backup_paths,
            estimated_improvement=improvement
        )

    def _is_actionable(self, issue: str) -> bool:
        """Check if issue is actionable (not just informational)"""
        non_actionable = [
            "monitor", "review", "check", "verify",
            "observe", "track", "watch"
        ]
        return not any(word in issue.lower() for word in non_actionable)

    def _log(self, message: str):
        """Print verbose log message"""
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)
```

---

## 3. Optimization Strategies by Category

### 3.1 CPU Optimizations

```python
def generate_cpu_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Generate CPU-specific optimization actions.

    Strategy:
    1. High CPU usage → Identify and limit heavy processes
    2. Thermal throttling → Reduce CPU intensive tasks
    3. Unbalanced cores → CPU affinity optimization
    4. Turbo boost → Enable/disable based on temperature
    """
    actions = []

    cpu_usage = metrics.get("total_usage", 0)
    temperature = metrics.get("temperature", 0)

    # High CPU usage optimization
    if cpu_usage > 80:
        top_processes = metrics.get("top_processes", [])
        if top_processes:
            heaviest = top_processes[0]
            pid = heaviest.get("pid")

            actions.append(OptimizationAction(
                command=f"renice +10 {pid}",
                description=f"Reduce priority of process {heaviest.get('name')} (PID {pid})",
                requires_sudo=False,
                reversible=True,
                rollback_command=f"renice +0 {pid}",
                verification_command=f"ps -p {pid} -o ni="
            ))

    # Thermal optimization
    if temperature > 80:
        actions.append(OptimizationAction(
            command="pmset -a reducebright 1",
            description="Reduce display brightness to lower temperature",
            requires_sudo=True,
            reversible=True,
            rollback_command="pmset -a reducebright 0",
            verification_command="pmset -g | grep reducebright"
        ))

    return actions
```

### 3.2 Memory Optimizations

```python
def generate_memory_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Memory optimization strategies.

    Strategy:
    1. High memory pressure → Purge inactive memory
    2. Excessive swap → Increase swap space or RAM
    3. Memory leaks → Identify and restart leaky processes
    """
    actions = []

    memory_percent = metrics.get("percent", 0)
    swap_used = metrics.get("swap_used_gb", 0)

    # High memory usage
    if memory_percent > 85:
        actions.append(OptimizationAction(
            command="sudo purge",
            description="Purge inactive memory and free up RAM",
            requires_sudo=True,
            reversible=False,  # Cannot undo purge
            rollback_command=None,
            verification_command="vm_stat | grep 'Pages free'"
        ))

    # Excessive swap
    if swap_used > 8:
        actions.append(OptimizationAction(
            command="sudo sysctl vm.swappiness=10",
            description="Reduce swap aggressiveness (swappiness=10)",
            requires_sudo=True,
            reversible=True,
            rollback_command="sudo sysctl vm.swappiness=60",
            verification_command="sysctl vm.swappiness"
        ))

    return actions
```

### 3.3 Disk Optimizations

```python
def generate_disk_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Disk optimization strategies.

    Strategy:
    1. High disk usage → Cleanup logs, caches, downloads
    2. Slow I/O → Enable TRIM for SSD
    3. Fragmentation → Defragmentation (if HFS+)
    """
    actions = []

    disk_percent = metrics.get("percent", 0)

    # High disk usage
    if disk_percent > 90:
        actions.append(OptimizationAction(
            command="rm -rf ~/Library/Caches/*",
            description="Clear user cache directory to free disk space",
            requires_sudo=False,
            reversible=False,  # Cannot restore deleted cache
            rollback_command=None,
            verification_command="du -sh ~/Library/Caches"
        ))

    # Enable TRIM for SSD
    actions.append(OptimizationAction(
        command="sudo trimforce enable",
        description="Enable TRIM for SSD performance",
        requires_sudo=True,
        reversible=True,
        rollback_command="sudo trimforce disable",
        verification_command="system_profiler SPSerialATADataType | grep TRIM"
    ))

    return actions
```

### 3.4 Network Optimizations

```python
def generate_network_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Network optimization strategies.

    Strategy:
    1. High error rate → Reset network interfaces
    2. Slow DNS → Configure faster DNS servers
    3. TCP tuning → Adjust TCP buffer sizes
    """
    actions = []

    error_rate = metrics.get("error_rate", 0)

    # High error rate
    if error_rate > 1.0:
        actions.append(OptimizationAction(
            command="sudo ifconfig en0 down && sudo ifconfig en0 up",
            description="Reset primary network interface to fix errors",
            requires_sudo=True,
            reversible=False,  # Reset is not reversible
            rollback_command=None,
            verification_command="netstat -i | grep en0"
        ))

    # DNS optimization
    actions.append(OptimizationAction(
        command='networksetup -setdnsservers Wi-Fi 1.1.1.1 8.8.8.8',
        description="Configure fast DNS servers (Cloudflare + Google)",
        requires_sudo=False,
        reversible=True,
        rollback_command='networksetup -setdnsservers Wi-Fi "Empty"',
        verification_command="networksetup -getdnsservers Wi-Fi"
    ))

    return actions
```

### 3.5 Battery Optimizations

```python
def generate_battery_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Battery optimization strategies.

    Strategy:
    1. Low battery → Enable low power mode
    2. Fast drain → Reduce brightness, disable background apps
    3. Poor health → Optimize charging patterns
    """
    actions = []

    battery_percent = metrics.get("percent", 100)
    is_plugged = metrics.get("power_plugged", True)

    # Low battery
    if battery_percent < 20 and not is_plugged:
        actions.append(OptimizationAction(
            command="sudo pmset -b lowpowermode 1",
            description="Enable Low Power Mode to extend battery",
            requires_sudo=True,
            reversible=True,
            rollback_command="sudo pmset -b lowpowermode 0",
            verification_command="pmset -g | grep lowpowermode"
        ))

    # Reduce brightness
    actions.append(OptimizationAction(
        command="brightness 0.5",
        description="Reduce display brightness to 50%",
        requires_sudo=False,
        reversible=True,
        rollback_command="brightness 1.0",
        verification_command="brightness -l"
    ))

    return actions
```

### 3.6 Thermal Optimizations

```python
def generate_thermal_optimizations(metrics: Dict) -> List[OptimizationAction]:
    """
    Thermal optimization strategies.

    Strategy:
    1. High temperature → Reduce CPU intensive tasks
    2. Fan control → Adjust fan curves
    3. Thermal throttling → Reduce workload
    """
    actions = []

    temperature = metrics.get("temperature", 0)

    # High temperature
    if temperature > 80:
        actions.append(OptimizationAction(
            command="sudo pmset -a sleep 10",
            description="Set aggressive sleep mode to reduce heat",
            requires_sudo=True,
            reversible=True,
            rollback_command="sudo pmset -a sleep 30",
            verification_command="pmset -g | grep sleep"
        ))

    return actions
```

---

## 4. Prioritization Algorithm

```python
def calculate_priority_score(optimization: Optimization) -> float:
    """
    Priority scoring algorithm.

    Formula:
    Priority = (Impact × W_impact) + (Risk_Inverted × W_risk) + (Urgency × W_urgency)

    Weights:
    - Impact: 40% (most important - maximize benefit)
    - Risk: 30% (prefer low-risk actions)
    - Urgency: 30% (address critical issues first)

    Scoring:
    - Impact: high=3, medium=2, low=1
    - Risk (inverted): low=3, medium=2, high=1 (prefer low risk)
    - Urgency: critical=4, high=3, medium=2, low=1

    Output: 0.0-10.0 (normalized)

    Examples:
    - High impact, low risk, critical urgency = 10.0
    - Medium impact, medium risk, low urgency = 4.7
    - Low impact, high risk, low urgency = 2.0
    """
    # Map string values to numeric scores
    impact_scores = {"high": 3, "medium": 2, "low": 1}
    risk_scores = {"low": 3, "medium": 2, "high": 1}  # Inverted!
    urgency_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    # Extract scores
    impact = impact_scores.get(optimization.impact, 1)
    risk = risk_scores.get(optimization.risk, 1)
    urgency = urgency_scores.get(optimization.urgency, 1)

    # Apply weights
    weighted_score = (impact * 0.4) + (risk * 0.3) + (urgency * 0.3)

    # Normalize to 0-10 scale
    # Max possible: (3 × 0.4) + (3 × 0.3) + (4 × 0.3) = 1.2 + 0.9 + 1.2 = 3.3
    max_score = 3.3
    normalized = (weighted_score / max_score) * 10

    return round(normalized, 2)
```

**Priority Score Breakdown Table**:

| Impact | Risk | Urgency | Raw Score | Normalized Score | Priority Level |
|--------|------|---------|-----------|------------------|----------------|
| High | Low | Critical | 3.3 | 10.0 | 🔥 Critical |
| High | Low | High | 3.0 | 9.1 | 🔴 Very High |
| High | Medium | High | 2.7 | 8.2 | 🟠 High |
| Medium | Low | High | 2.7 | 8.2 | 🟠 High |
| High | Medium | Medium | 2.4 | 7.3 | 🟡 Medium-High |
| Medium | Medium | Medium | 2.0 | 6.1 | 🟢 Medium |
| Low | Low | Medium | 1.5 | 4.5 | 🔵 Low-Medium |
| Low | Medium | Low | 1.2 | 3.6 | ⚪ Low |
| Low | High | Low | 0.9 | 2.7 | ⚫ Very Low |

---

## 5. Risk Assessment Matrix

```python
def assess_optimization_risk(
    current_state: Dict,
    action_risk: str,
    rollback_support: bool
) -> str:
    """
    Determine overall risk level for an optimization.

    Decision Matrix:

    | Current State | Action Risk | Rollback | Overall Risk | Action |
    |---------------|-------------|----------|--------------|---------|
    | Critical      | High        | No       | BLOCK        | Reject  |
    | Critical      | High        | Yes      | HIGH         | Warn    |
    | Critical      | Medium      | Yes      | MEDIUM       | Allow   |
    | Critical      | Low         | Yes      | MEDIUM       | Allow   |
    | Warning       | High        | No       | HIGH         | Warn    |
    | Warning       | High        | Yes      | MEDIUM       | Allow   |
    | Warning       | Medium      | Yes      | LOW          | Allow   |
    | Warning       | Low         | Yes      | LOW          | Allow   |
    | Healthy       | Any         | Any      | LOW          | Allow   |

    Returns:
        "BLOCK", "HIGH", "MEDIUM", or "LOW"
    """
    status = current_state.get("status", "unknown")

    # BLOCK: Critical state + High risk + No rollback
    if status == "critical" and action_risk == "high" and not rollback_support:
        return "BLOCK"

    # HIGH: Critical state + High risk (but has rollback)
    if status == "critical" and action_risk == "high" and rollback_support:
        return "HIGH"

    # HIGH: Warning state + High risk + No rollback
    if status == "warning" and action_risk == "high" and not rollback_support:
        return "HIGH"

    # MEDIUM: Critical + Medium/Low risk, or Warning + High risk with rollback
    if status == "critical" and action_risk in ["medium", "low"]:
        return "MEDIUM"
    if status == "warning" and action_risk == "high" and rollback_support:
        return "MEDIUM"

    # LOW: Everything else (warning + low/medium risk, healthy state)
    return "LOW"
```

**Risk Blocking Rules**:

1. **BLOCK Immediately**: Critical state + High risk action + No rollback
2. **Warn User**: HIGH risk (require explicit confirmation)
3. **Allow**: MEDIUM and LOW risk (included in execution plan)

---

## 6. User Approval Workflow (Korean UI)

```python
from typing import List, Dict


def request_user_approval(plan: ExecutionPlan) -> Dict[str, bool]:
    """
    Request user approval for optimization plan using Korean UI.

    Uses MoAI AskUserQuestion for interactive approval.

    Returns:
        Dict mapping optimization IDs to approval status
    """
    # Prepare optimization summary
    top_optimizations = plan.optimizations[:5]  # Show top 5

    # Build question text in Korean
    question_text = f"""
최적화 계획을 검토해주세요:

총 {plan.total_count}개의 최적화 항목
├─ 높은 우선순위: {plan.high_priority_count}개
├─ 중간 우선순위: {plan.medium_priority_count}개
└─ 낮은 우선순위: {plan.low_priority_count}개

전체 위험도: {plan.risk_assessment.overall_risk.upper()}
예상 소요 시간: {plan.estimated_duration}
롤백 가능 비율: {plan.risk_assessment.reversibility_score}%

상위 5개 최적화:
"""

    for i, opt in enumerate(top_optimizations, 1):
        question_text += f"""
{i}. [{opt.category.upper()}] {opt.issue}
   • 영향도: {opt.impact.upper()}
   • 위험도: {opt.risk.upper()}
   • 우선순위: {opt.priority_score}/10
   • 롤백: {'가능' if opt.rollback_supported else '불가능'}
   • 예상 개선: {opt.estimated_improvement}
"""

    if plan.total_count > 5:
        question_text += f"\n... 외 {plan.total_count - 5}개 항목\n"

    question_text += "\n어떻게 진행하시겠습니까?"

    # Use AskUserQuestion for approval
    from moai_adk import AskUserQuestion

    response = AskUserQuestion({
        "questions": [{
            "question": question_text,
            "header": "최적화 실행",
            "multiSelect": False,
            "options": [
                {
                    "label": "전체 실행",
                    "description": f"모든 {plan.total_count}개 최적화를 순차적으로 실행합니다 (백업 생성 후)"
                },
                {
                    "label": "상위 5개만 실행",
                    "description": "우선순위가 가장 높은 5개 항목만 실행합니다"
                },
                {
                    "label": "미리보기 (Dry-run)",
                    "description": "실제 변경 없이 예상 결과만 확인합니다"
                },
                {
                    "label": "건너뛰기",
                    "description": "최적화를 실행하지 않고 종료합니다"
                }
            ]
        }]
    })

    # Parse user choice
    choice = response["answers"].get("최적화 실행", "건너뛰기")

    approvals = {}
    if choice == "전체 실행":
        for opt in plan.optimizations:
            approvals[opt.id] = True
    elif choice == "상위 5개만 실행":
        for opt in plan.optimizations[:5]:
            approvals[opt.id] = True
    elif choice == "미리보기 (Dry-run)":
        # Return empty approvals (triggers dry-run mode)
        approvals = {}
    else:  # 건너뛰기
        approvals = {}

    return approvals
```

**Approval Flow Diagram**:

```
User Question (Korean)
       ↓
┌──────────────────────┐
│  최적화 실행 선택       │
├──────────────────────┤
│ ○ 전체 실행            │ → Execute all optimizations
│ ○ 상위 5개만 실행      │ → Execute top 5 only
│ ○ 미리보기 (Dry-run)  │ → Show preview without changes
│ ○ 건너뛰기             │ → Exit without changes
└──────────────────────┘
       ↓
Parse User Choice
       ↓
Return Approval Dict
```

---

## 7. Execution Modes

### 7.1 Dry-Run Mode (Default)

```python
def execute_dry_run(plan: ExecutionPlan) -> Dict:
    """
    Simulate optimizations without making changes.

    Returns:
        Preview report with expected changes
    """
    preview_results = []

    for opt in plan.optimizations:
        preview = {
            "id": opt.id,
            "category": opt.category,
            "issue": opt.issue,
            "priority_score": opt.priority_score,

            "current_state": opt.current_state,
            "target_state": opt.target_state,

            "actions_to_execute": [
                {
                    "command": action.command,
                    "description": action.description,
                    "requires_sudo": action.requires_sudo
                }
                for action in opt.actions
            ],

            "expected_improvement": opt.estimated_improvement,
            "rollback_available": opt.rollback_supported,

            "would_execute": True  # Dry-run simulation
        }
        preview_results.append(preview)

    return {
        "mode": "dry-run",
        "timestamp": datetime.now().isoformat(),
        "total_optimizations": len(preview_results),
        "preview": preview_results,
        "note": "This is a simulation. No changes were made to the system."
    }
```

### 7.2 Apply Mode (--apply flag)

```python
def execute_apply_mode(
    plan: ExecutionPlan,
    approvals: Dict[str, bool]
) -> Dict:
    """
    Execute approved optimizations with backup and verification.

    Args:
        plan: Execution plan with all optimizations
        approvals: Dict of optimization IDs approved by user

    Returns:
        Execution results with success/failure details
    """
    import subprocess
    from pathlib import Path

    # Create backup directory
    if plan.backup_directory:
        backup_path = Path(plan.backup_directory)
        backup_path.mkdir(parents=True, exist_ok=True)

    results = []
    successful = 0
    failed = 0

    for opt in plan.optimizations:
        # Skip if not approved
        if not approvals.get(opt.id, False):
            results.append({
                "id": opt.id,
                "status": "skipped",
                "reason": "Not approved by user"
            })
            continue

        # Backup files if needed
        if opt.backup_needed and plan.backup_directory:
            for backup_file in opt.backup_paths:
                try:
                    # Copy file to backup directory
                    src = Path(backup_file)
                    dst = Path(plan.backup_directory) / src.name
                    if src.exists():
                        shutil.copy2(src, dst)
                except Exception as e:
                    results.append({
                        "id": opt.id,
                        "status": "failed",
                        "reason": f"Backup failed: {e}"
                    })
                    failed += 1
                    continue

        # Execute actions sequentially
        action_results = []
        all_success = True

        for action in opt.actions:
            try:
                # Execute command
                result = subprocess.run(
                    action.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Verify if verification command exists
                verification_passed = True
                if action.verification_command:
                    verify_result = subprocess.run(
                        action.verification_command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    verification_passed = (verify_result.returncode == 0)

                action_results.append({
                    "command": action.command,
                    "description": action.description,
                    "success": result.returncode == 0,
                    "verification_passed": verification_passed,
                    "output": result.stdout[:200]  # Truncate
                })

                if result.returncode != 0 or not verification_passed:
                    all_success = False

                    # Rollback if supported
                    if action.rollback_command:
                        subprocess.run(
                            action.rollback_command,
                            shell=True,
                            capture_output=True,
                            timeout=30
                        )
                    break

            except Exception as e:
                action_results.append({
                    "command": action.command,
                    "description": action.description,
                    "success": False,
                    "error": str(e)
                })
                all_success = False
                break

        # Record overall result
        if all_success:
            successful += 1
            status = "success"
        else:
            failed += 1
            status = "failed"

        results.append({
            "id": opt.id,
            "category": opt.category,
            "issue": opt.issue,
            "status": status,
            "actions": action_results,
            "execution_time": datetime.now().isoformat()
        })

    return {
        "mode": "apply",
        "timestamp": datetime.now().isoformat(),
        "total_approved": len(approvals),
        "successful": successful,
        "failed": failed,
        "backup_directory": plan.backup_directory,
        "results": results
    }
```

---

## 8. Output Format

### 8.1 JSON Output (--json flag)

```json
{
  "timestamp": "2025-12-01T10:30:00",
  "mode": "dry-run",
  "analysis_summary": {
    "overall_status": "warning",
    "health_score": 75.5,
    "categories_analyzed": 6
  },
  "optimizations": [
    {
      "id": "opt-001",
      "priority_score": 9.1,
      "category": "cpu",
      "issue": "High CPU usage detected (87.3%)",
      "current_state": {
        "total_usage": 87.3,
        "temperature": 82.5,
        "status": "warning"
      },
      "target_state": {
        "total_usage": 65.0,
        "temperature": 75.0,
        "status": "healthy"
      },
      "actions": [
        {
          "command": "renice +10 1234",
          "description": "Reduce priority of process chrome (PID 1234)",
          "requires_sudo": false
        }
      ],
      "impact": "high",
      "risk": "low",
      "urgency": "high",
      "rollback_supported": true,
      "estimated_improvement": "15-20% CPU reduction"
    },
    {
      "id": "opt-002",
      "priority_score": 8.2,
      "category": "memory",
      "issue": "Memory pressure critical (92% used)",
      "current_state": {
        "percent": 92.0,
        "swap_used_gb": 12.5,
        "status": "critical"
      },
      "target_state": {
        "percent": 75.0,
        "swap_used_gb": 4.0,
        "status": "healthy"
      },
      "actions": [
        {
          "command": "sudo purge",
          "description": "Purge inactive memory",
          "requires_sudo": true
        }
      ],
      "impact": "high",
      "risk": "medium",
      "urgency": "critical",
      "rollback_supported": false,
      "estimated_improvement": "10-15% memory freed"
    }
  ],
  "execution_plan": {
    "total_count": 12,
    "high_priority_count": 4,
    "medium_priority_count": 5,
    "low_priority_count": 3,
    "estimated_duration": "10-30 minutes"
  },
  "risk_assessment": {
    "overall_risk": "medium",
    "blocked_optimizations": [],
    "warnings": [
      "opt-002: Memory purge cannot be rolled back"
    ],
    "requires_backup": true,
    "requires_sudo": true,
    "reversibility_score": 83.3
  }
}
```

### 8.2 Human-Readable Output (Default)

```
🔧 System Optimization Report
==============================================================================

📊 Analysis Summary:
   Overall Status: ⚠️  WARNING
   Health Score: 75.5/100
   Categories Analyzed: 6

🎯 Optimization Plan:
   Total Recommendations: 12
   ├─ High Priority: 4
   ├─ Medium Priority: 5
   └─ Low Priority: 3

   Estimated Duration: 10-30 minutes
   Overall Risk: MEDIUM
   Rollback Support: 83.3%

------------------------------------------------------------------------------
Top 5 Optimizations (by priority):
------------------------------------------------------------------------------

1. [CPU] High CPU usage detected (87.3%)
   Priority: 9.1/10 | Impact: HIGH | Risk: LOW | Urgency: HIGH

   Current State:
   • Total Usage: 87.3%
   • Temperature: 82.5°C
   • Status: WARNING

   Target State:
   • Total Usage: ~65%
   • Temperature: ~75°C
   • Status: HEALTHY

   Actions:
   ✓ Reduce priority of process chrome (PID 1234)

   Expected Improvement: 15-20% CPU reduction
   Rollback Available: ✅ Yes

------------------------------------------------------------------------------

2. [MEMORY] Memory pressure critical (92% used)
   Priority: 8.2/10 | Impact: HIGH | Risk: MEDIUM | Urgency: CRITICAL

   Current State:
   • Memory Used: 92%
   • Swap Used: 12.5 GB
   • Status: CRITICAL

   Target State:
   • Memory Used: ~75%
   • Swap Used: ~4 GB
   • Status: HEALTHY

   Actions:
   ⚠️  Purge inactive memory (requires sudo)

   Expected Improvement: 10-15% memory freed
   Rollback Available: ❌ No

------------------------------------------------------------------------------

... (3 more optimizations)

⚠️  Risk Warnings:
   • opt-002: Memory purge cannot be rolled back
   • Backup recommended before execution
   • Sudo access required for 7 actions

💡 Next Steps:
   1. Review the optimization plan
   2. Run with --apply to execute approved optimizations
   3. Run with --dry-run to preview changes without execution
   4. Use --top-n 10 to see more recommendations

Example:
   uv run optimize.py < analysis.json --apply
```

---

## 9. Dependencies & Integration

### 9.1 Input Dependencies

```python
# Input: analyze_all.py JSON output
required_input_structure = {
    "timestamp": "ISO 8601 datetime",
    "categories": {
        "cpu": {"metrics": {...}, "analysis": {...}},
        "memory": {...},
        "disk": {...},
        "network": {...},
        "battery": {...},
        "thermal": {...}
    },
    "overall": {
        "status": "healthy|warning|critical",
        "risk_level": "low|medium|high|critical",
        "health_score": float  # 0-100
    }
}
```

### 9.2 External Tool Dependencies

```python
# macOS system commands used
required_commands = [
    "renice",         # Process priority
    "pmset",          # Power management
    "purge",          # Memory management
    "trimforce",      # SSD TRIM
    "networksetup",   # Network configuration
    "ifconfig",       # Network interfaces
    "sysctl",         # Kernel parameters
    "brightness",     # Display brightness (may need install)
]

# Check availability
def check_dependencies():
    """Verify required system commands are available"""
    missing = []
    for cmd in required_commands:
        result = subprocess.run(
            f"which {cmd}",
            shell=True,
            capture_output=True
        )
        if result.returncode != 0:
            missing.append(cmd)

    if missing:
        raise RuntimeError(f"Missing commands: {', '.join(missing)}")
```

### 9.3 MoAI Integration

```python
# AskUserQuestion for user approval
from moai_adk import AskUserQuestion

# Example usage
response = AskUserQuestion({
    "questions": [{
        "question": "최적화를 실행하시겠습니까?",
        "header": "최적화 실행",
        "multiSelect": False,
        "options": [...]
    }]
})
```

---

## 10. Performance Targets

```python
# Performance benchmarks
performance_targets = {
    "analysis_parsing": {
        "target": "< 0.5 seconds",
        "measurement": "Time to load and validate JSON"
    },

    "optimization_generation": {
        "target": "< 1.0 seconds",
        "measurement": "Time to generate all optimizations"
    },

    "prioritization": {
        "target": "< 0.5 seconds",
        "measurement": "Time to calculate priority scores"
    },

    "total_dry_run": {
        "target": "< 2.5 seconds",
        "measurement": "End-to-end dry-run execution"
    },

    "user_approval_workflow": {
        "target": "< 5.0 seconds",
        "measurement": "Display approval UI + get response"
    },

    "single_optimization_execution": {
        "target": "< 30 seconds",
        "measurement": "Execute one optimization with verification"
    }
}
```

**Performance Optimization Strategies**:

1. **Lazy Loading**: Only load heavy dependencies when needed
2. **Parallel Execution**: Execute independent optimizations concurrently
3. **Caching**: Cache expensive computations (priority scores, risk assessments)
4. **Early Exit**: Skip blocked optimizations immediately
5. **Timeout Limits**: All subprocess calls have 30s timeout

---

## 11. Error Handling & Rollback

```python
class OptimizationError(Exception):
    """Base exception for optimization errors"""
    pass


class BackupError(OptimizationError):
    """Backup creation failed"""
    pass


class ExecutionError(OptimizationError):
    """Optimization execution failed"""
    pass


class VerificationError(OptimizationError):
    """Verification check failed"""
    pass


def safe_execute_with_rollback(
    optimization: Optimization
) -> Dict:
    """
    Execute optimization with automatic rollback on failure.

    Returns:
        Execution result dict
    """
    executed_actions = []

    try:
        # Execute each action
        for action in optimization.actions:
            result = subprocess.run(
                action.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise ExecutionError(f"Command failed: {action.command}")

            # Verify if possible
            if action.verification_command:
                verify = subprocess.run(
                    action.verification_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if verify.returncode != 0:
                    raise VerificationError(f"Verification failed: {action.verification_command}")

            executed_actions.append(action)

        return {
            "status": "success",
            "executed_actions": len(executed_actions),
            "optimization_id": optimization.id
        }

    except Exception as e:
        # Rollback all executed actions (in reverse order)
        rollback_results = []
        for action in reversed(executed_actions):
            if action.rollback_command:
                try:
                    subprocess.run(
                        action.rollback_command,
                        shell=True,
                        capture_output=True,
                        timeout=30
                    )
                    rollback_results.append({
                        "action": action.description,
                        "rollback": "success"
                    })
                except Exception as rb_error:
                    rollback_results.append({
                        "action": action.description,
                        "rollback": "failed",
                        "error": str(rb_error)
                    })

        return {
            "status": "failed",
            "error": str(e),
            "executed_actions": len(executed_actions),
            "rollback_attempted": len(rollback_results),
            "rollback_results": rollback_results,
            "optimization_id": optimization.id
        }
```

---

## 12. CLI Interface Design

```python
@click.command()
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON instead of human-readable format')
@click.option('--apply', is_flag=True,
              help='Execute optimizations (default: dry-run mode)')
@click.option('--top-n', type=int, default=5,
              help='Number of top optimizations to show (default: 5)')
@click.option('--category', type=click.Choice(['cpu', 'memory', 'disk', 'network', 'battery', 'thermal', 'all']),
              default='all',
              help='Filter by category (default: all)')
@click.option('--min-priority', type=float, default=0.0,
              help='Minimum priority score (0.0-10.0, default: 0.0)')
@click.option('--skip-approval', is_flag=True,
              help='Skip user approval (use with caution!)')
@click.option('--backup-dir', type=click.Path(),
              default=None,
              help='Custom backup directory (default: auto-generated)')
@click.option('--verbose', is_flag=True,
              help='Show detailed execution logs')
@click.argument('analysis_file', type=click.File('r'), default=sys.stdin)
def main(
    output_json: bool,
    apply: bool,
    top_n: int,
    category: str,
    min_priority: float,
    skip_approval: bool,
    backup_dir: Optional[str],
    verbose: bool,
    analysis_file
):
    """
    Generate and execute system optimizations based on analysis results.

    Examples:
        # Dry-run mode (default)
        uv run analyze_all.py --json | uv run optimize.py

        # Execute optimizations
        uv run analyze_all.py --json | uv run optimize.py --apply

        # Show top 10 CPU optimizations only
        uv run optimize.py --category cpu --top-n 10 < analysis.json

        # Execute high-priority optimizations only
        uv run optimize.py --apply --min-priority 7.0 < analysis.json
    """
    pass
```

---

## 13. Testing Strategy

### Unit Tests

```python
def test_priority_calculation():
    """Test priority score calculation"""
    opt = Optimization(
        id="test-001",
        category="cpu",
        issue="High CPU",
        impact="high",
        risk="low",
        urgency="critical",
        # ... other fields
    )

    score = calculate_priority_score(opt)
    assert score == 10.0, f"Expected 10.0, got {score}"


def test_risk_assessment():
    """Test risk assessment matrix"""
    risk = assess_optimization_risk(
        current_state={"status": "critical"},
        action_risk="high",
        rollback_support=False
    )
    assert risk == "BLOCK", f"Expected BLOCK, got {risk}"
```

### Integration Tests

```python
def test_end_to_end_dry_run():
    """Test complete dry-run workflow"""
    # Load sample analysis
    analysis = load_test_analysis()

    # Create engine
    engine = OptimizationEngine(analysis, verbose=False)

    # Generate optimizations
    engine.load_analysis_results()
    engine.generate_optimizations()
    engine.prioritize_recommendations()
    engine.assess_risks()

    # Create execution plan
    plan = engine.create_execution_plan()

    # Execute dry-run
    result = execute_dry_run(plan)

    assert result["mode"] == "dry-run"
    assert result["total_optimizations"] > 0
```

---

## 14. Future Enhancements

### Phase 3 Additions (Future)

1. **Machine Learning Priority Scoring**:
   - Learn from user approval patterns
   - Adjust weights based on historical effectiveness
   - Personalized recommendation ranking

2. **Automated Scheduling**:
   - Schedule low-priority optimizations during idle time
   - Periodic re-analysis and optimization
   - Integration with macOS launchd

3. **Advanced Rollback**:
   - Snapshot-based rollback (Time Machine integration)
   - Multi-step rollback coordination
   - Rollback verification and validation

4. **Performance Tracking**:
   - Before/after metrics comparison
   - Effectiveness scoring per optimization
   - Long-term trend analysis

5. **Multi-System Support**:
   - Linux optimization strategies
   - Windows optimization (future)
   - Cross-platform optimization engine

---

## Summary

This algorithm design provides a complete blueprint for implementing `optimize.py` with:

✅ **Clear data flow**: Input → Parse → Generate → Prioritize → Approve → Execute → Output
✅ **Robust data models**: Optimization, RiskAssessment, ExecutionPlan classes
✅ **Category-specific strategies**: CPU, Memory, Disk, Network, Battery, Thermal optimizations
✅ **Intelligent prioritization**: Impact × Risk × Urgency scoring algorithm
✅ **Risk-aware execution**: Risk assessment matrix with BLOCK/HIGH/MEDIUM/LOW levels
✅ **User-friendly workflow**: Korean UI with AskUserQuestion integration
✅ **Dual execution modes**: Dry-run (preview) and Apply (execute with backup/rollback)
✅ **Production-ready error handling**: Automatic rollback on failure
✅ **Performance optimized**: Target < 2.5s for dry-run, < 30s per optimization
✅ **Comprehensive testing**: Unit and integration test strategies

**Next Steps for Phase 2 Day 4 Implementation**:
1. Implement core data models (Optimization, OptimizationAction, etc.)
2. Implement OptimizationEngine class
3. Implement category-specific optimization generators
4. Implement prioritization and risk assessment
5. Implement user approval workflow
6. Implement dry-run and apply execution modes
7. Write unit tests and integration tests
8. Create CLI interface with click
9. Integration testing with real analyze_all.py output

**Estimated Implementation Time**: 6-8 hours (1 full day)

---

**Document Status**: ✅ Complete - Ready for Implementation
**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Author**: MoAI-ADK Backend Expert Agent
