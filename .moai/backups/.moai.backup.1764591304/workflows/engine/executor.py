"""
Workflow Executor - Main Orchestration Engine

Orchestrates workflow execution with:
- DAG-based phase ordering
- Sequential and parallel execution
- Resource-aware dynamic parallelism
- State tracking integration
- Checkpoint creation

This is the central workflow engine inspired by BMAD patterns.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .coordinator import AgentCoordinator, AgentTask, PhaseResult, AgentStatus
from .resource_monitor import ResourceMonitor, ParallelismRecommendation


@dataclass
class WorkflowMetadata:
    """Workflow metadata from TOON file"""
    template_id: str
    name: str
    complexity: str
    file_count: str
    agent_count: str


@dataclass
class Phase:
    """Workflow phase definition"""
    id: int
    agents: list[str]
    mode: str  # "sequential" | "parallel"
    dependencies: list[int]
    max_parallel: int
    description: str


@dataclass
class ExecutionStrategy:
    """Workflow execution strategy"""
    mode: str  # "sequential" | "mixed" | "parallel" | "hybrid"
    parallel_default: int
    dynamic_adjust: bool
    max_concurrent: int


@dataclass
class WorkflowDefinition:
    """Complete workflow definition (from TOON parser)"""
    metadata: WorkflowMetadata
    phases: list[Phase]
    exec_strategy: ExecutionStrategy
    files: list[dict[str, str]] = field(default_factory=list)
    agent_pool: list[dict[str, Any]] = field(default_factory=list)
    quality_gates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Workflow execution result"""
    workflow_id: str
    status: str  # "completed" | "failed" | "partial"
    total_phases: int
    completed_phases: int
    failed_phases: int
    total_time: float
    phase_results: list[PhaseResult]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class WorkflowExecutor:
    """
    Main workflow orchestration engine

    Usage:
        executor = WorkflowExecutor(
            workflow=workflow_def,
            token_budget=150000
        )

        result = await executor.execute()

        if result.status == "completed":
            print(f"Workflow completed in {result.total_time:.1f}s")
        else:
            print(f"Workflow failed: {result.errors}")
    """

    def __init__(
        self,
        workflow: WorkflowDefinition,
        token_budget: int = 150000,
        enable_resource_monitoring: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize workflow executor

        Args:
            workflow: Parsed workflow definition
            token_budget: Token usage threshold
            enable_resource_monitoring: Enable dynamic parallelism adjustment
            max_retries: Max retry attempts for failed agents
        """
        self.workflow = workflow
        self.token_budget = token_budget
        self.enable_resource_monitoring = enable_resource_monitoring
        self.max_retries = max_retries

        # Initialize components
        self.coordinator = AgentCoordinator(max_retries=max_retries)
        self.resource_monitor = ResourceMonitor(token_threshold=token_budget)

        # Execution state
        self.current_token_usage = 0
        self.current_parallel = workflow.exec_strategy.parallel_default
        self.phase_results: list[PhaseResult] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def resolve_dag(self) -> list[list[int]]:
        """
        Resolve phase dependencies into execution order (topological sort)

        Returns:
            List of phase batches (each batch can run in parallel)

        Example:
            Phase 1: deps=[]
            Phase 2: deps=[1]
            Phase 3: deps=[1]
            Phase 4: deps=[2,3]

            Result: [[1], [2, 3], [4]]
        """
        phases = {p.id: p for p in self.workflow.phases}
        in_degree = {p.id: len(p.dependencies) for p in self.workflow.phases}
        execution_order: list[list[int]] = []

        # Topological sort using Kahn's algorithm
        while phases:
            # Find all phases with in_degree 0 (ready to execute)
            ready = [pid for pid, degree in in_degree.items() if degree == 0]

            if not ready:
                # Circular dependency detected
                remaining = list(phases.keys())
                self.errors.append(
                    f"Circular dependency detected in phases: {remaining}"
                )
                return execution_order

            execution_order.append(ready)

            # Remove ready phases
            for pid in ready:
                del phases[pid]
                del in_degree[pid]

                # Decrease in_degree for dependent phases
                for remaining_id in list(phases.keys()):
                    remaining_phase = phases[remaining_id]
                    if pid in remaining_phase.dependencies:
                        in_degree[remaining_id] -= 1

        return execution_order

    async def execute_phase_batch(
        self,
        phase_ids: list[int],
        prompt_context: dict[str, Any]
    ) -> list[PhaseResult]:
        """
        Execute a batch of phases (all have dependencies satisfied)

        Args:
            phase_ids: Phase IDs to execute
            prompt_context: Context data for prompt generation

        Returns:
            List of PhaseResult for each phase
        """
        results = []

        for phase_id in phase_ids:
            phase = next(p for p in self.workflow.phases if p.id == phase_id)

            # Generate phase prompt
            prompt = self._generate_phase_prompt(phase, prompt_context)

            # Check resource usage before execution
            if self.enable_resource_monitoring:
                recommendation = self.resource_monitor.check_resources(
                    current_parallel=self.current_parallel,
                    token_usage=self.current_token_usage
                )

                if recommendation:
                    self._apply_recommendation(recommendation)

            # Execute phase with coordinator
            result = await self.coordinator.execute_phase(
                phase_id=phase.id,
                agents=phase.agents,
                prompt_template=prompt,
                mode=phase.mode,
                max_parallel=min(phase.max_parallel, self.current_parallel)
            )

            results.append(result)

            # Update token usage (estimate based on execution time)
            # Real implementation would get actual token count from agents
            self.current_token_usage += self._estimate_token_usage(result)

            # Stop batch if phase failed and has dependents
            if result.status == "failed":
                self.errors.append(
                    f"Phase {phase_id} failed: {result.errors}"
                )
                # Check if any remaining phases depend on this one
                has_dependents = any(
                    phase_id in p.dependencies
                    for p in self.workflow.phases
                    if p.id in phase_ids[phase_ids.index(phase_id)+1:]
                )
                if has_dependents:
                    break

        return results

    async def execute(self) -> ExecutionResult:
        """
        Execute complete workflow

        Returns:
            ExecutionResult with final status
        """
        import time
        start_time = time.time()

        # Resolve DAG
        execution_order = self.resolve_dag()

        if self.errors:
            # DAG resolution failed
            return ExecutionResult(
                workflow_id=self.workflow.metadata.template_id,
                status="failed",
                total_phases=len(self.workflow.phases),
                completed_phases=0,
                failed_phases=0,
                total_time=time.time() - start_time,
                phase_results=[],
                errors=self.errors
            )

        # Execute phases in DAG order
        for batch_idx, phase_batch in enumerate(execution_order):
            batch_results = await self.execute_phase_batch(
                phase_ids=phase_batch,
                prompt_context={
                    "batch": batch_idx,
                    "workflow_name": self.workflow.metadata.name
                }
            )

            self.phase_results.extend(batch_results)

            # Check for critical failures
            failed_in_batch = [r for r in batch_results if r.status == "failed"]
            if failed_in_batch:
                # Check if we should continue or stop
                critical_failure = any(
                    any(p.id in phase_batch for p in self.workflow.phases
                        if remaining_id in p.dependencies)
                    for remaining_batch in execution_order[batch_idx+1:]
                    for remaining_id in remaining_batch
                )

                if critical_failure:
                    self.errors.append(
                        f"Critical failure in batch {batch_idx}: "
                        f"phases {phase_batch} - stopping execution"
                    )
                    break

        # Calculate final statistics
        total_time = time.time() - start_time
        completed = len([r for r in self.phase_results if r.status == "completed"])
        failed = len([r for r in self.phase_results if r.status == "failed"])

        if failed == 0:
            status = "completed"
        elif completed == 0:
            status = "failed"
        else:
            status = "partial"

        return ExecutionResult(
            workflow_id=self.workflow.metadata.template_id,
            status=status,
            total_phases=len(self.workflow.phases),
            completed_phases=completed,
            failed_phases=failed,
            total_time=total_time,
            phase_results=self.phase_results,
            errors=self.errors,
            warnings=self.warnings
        )

    def _generate_phase_prompt(
        self,
        phase: Phase,
        context: dict[str, Any]
    ) -> str:
        """
        Generate prompt for phase execution

        Args:
            phase: Phase definition
            context: Execution context

        Returns:
            Prompt string for agents
        """
        # Base prompt template
        prompt = f"""
Execute Phase {phase.id}: {phase.description}

Workflow: {context.get('workflow_name', 'Unknown')}
Mode: {phase.mode}
Agents: {', '.join(phase.agents)}

Task: {phase.description}

Please complete this phase following TRUST 5 principles.
""".strip()

        return prompt

    def _estimate_token_usage(self, result: PhaseResult) -> int:
        """
        Estimate token usage from phase result

        Args:
            result: PhaseResult

        Returns:
            Estimated tokens used

        Note:
            This is a rough estimate based on execution time.
            Real implementation would get actual token counts from agents.
        """
        # Rough estimate: 1000 tokens per agent per minute
        tokens_per_second = 1000 / 60
        total_time = sum(r.execution_time for r in result.agent_results)
        return int(total_time * tokens_per_second)

    def _apply_recommendation(self, rec: ParallelismRecommendation):
        """
        Apply resource monitoring recommendation

        Args:
            rec: ParallelismRecommendation from resource monitor
        """
        old_parallel = self.current_parallel
        self.current_parallel = rec.recommended_parallel

        if rec.severity == "critical":
            self.warnings.append(
                f"⚠️  {rec.reason} - reducing parallelism "
                f"{old_parallel} → {self.current_parallel}"
            )
        elif rec.severity == "info" and rec.recommended_parallel > old_parallel:
            self.warnings.append(
                f"✅ Resources healthy - increasing parallelism "
                f"{old_parallel} → {self.current_parallel}"
            )


# Module-level convenience function
async def execute_workflow(
    workflow: WorkflowDefinition,
    token_budget: int = 150000
) -> ExecutionResult:
    """
    Execute a workflow with default settings

    Args:
        workflow: Parsed workflow definition
        token_budget: Token usage threshold

    Returns:
        ExecutionResult with final status

    Example:
        from .toon_workflow_parser import parse_workflow

        workflow = parse_workflow(toon_content)
        result = await execute_workflow(workflow, token_budget=120000)

        if result.status == "completed":
            print(f"Success! Completed {result.completed_phases} phases")
    """
    executor = WorkflowExecutor(
        workflow=workflow,
        token_budget=token_budget
    )

    return await executor.execute()


# CLI entry point for testing
if __name__ == "__main__":
    import sys

    async def main():
        # Example usage
        print("Workflow Executor - Test Mode")
        print("=" * 50)

        # Create test workflow
        test_workflow = WorkflowDefinition(
            metadata=WorkflowMetadata(
                template_id="TEST-001",
                name="Test Workflow",
                complexity="simple",
                file_count="1-3",
                agent_count="1"
            ),
            phases=[
                Phase(
                    id=1,
                    agents=["expert-backend"],
                    mode="sequential",
                    dependencies=[],
                    max_parallel=1,
                    description="Test phase 1"
                )
            ],
            exec_strategy=ExecutionStrategy(
                mode="sequential",
                parallel_default=1,
                dynamic_adjust=False,
                max_concurrent=1
            )
        )

        result = await execute_workflow(test_workflow)

        print(f"\nResult: {result.status}")
        print(f"Phases: {result.completed_phases}/{result.total_phases}")
        print(f"Time: {result.total_time:.2f}s")

        if result.errors:
            print(f"\nErrors: {result.errors}")

    asyncio.run(main())
