"""
Agent Coordinator for Workflow Execution

Handles agent delegation via Task(), result collection, MCP resume chains,
and error recovery for workflow phases.

Key Features:
- Agent delegation with Task() integration
- Result collection and validation
- MCP resume chain support for multi-day workflows
- Retry logic with exponential backoff
- Structured error reporting
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Literal
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AgentTask:
    """Agent task definition"""
    agent: str
    phase_id: int
    prompt: str
    model: Optional[str] = None
    resume_id: Optional[str] = None  # MCP resume chain


@dataclass
class AgentResult:
    """Agent execution result"""
    agent: str
    phase_id: int
    status: AgentStatus
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    retry_count: int = 0
    resume_id: Optional[str] = None  # For MCP resume


@dataclass
class PhaseResult:
    """Phase execution result"""
    phase_id: int
    status: Literal["completed", "failed", "partial"]
    agent_results: list[AgentResult]
    execution_time: float
    errors: list[str] = field(default_factory=list)


class AgentCoordinator:
    """
    Coordinate agent delegation and result collection

    Usage:
        coordinator = AgentCoordinator(max_retries=2)

        # Sequential execution
        result = await coordinator.execute_agent(
            agent="expert-backend",
            phase_id=1,
            prompt="Implement user authentication API"
        )

        # Parallel execution
        tasks = [
            AgentTask("expert-backend", 2, "Implement API endpoints"),
            AgentTask("expert-frontend", 2, "Implement UI components")
        ]
        results = await coordinator.execute_parallel(tasks, max_concurrent=2)
    """

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 5.0,
        timeout_seconds: Optional[float] = None
    ):
        """
        Initialize agent coordinator

        Args:
            max_retries: Maximum retry attempts for failed agents
            retry_delay: Base delay (seconds) between retries (exponential backoff)
            timeout_seconds: Optional timeout for agent execution
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout_seconds = timeout_seconds
        self.active_tasks: dict[str, AgentTask] = {}
        self.results_cache: dict[str, AgentResult] = {}

    async def execute_agent(
        self,
        agent: str,
        phase_id: int,
        prompt: str,
        model: Optional[str] = None,
        resume_id: Optional[str] = None
    ) -> AgentResult:
        """
        Execute a single agent task

        Args:
            agent: Agent identifier (e.g., "expert-backend")
            phase_id: Phase number
            prompt: Task description for agent
            model: Optional model override
            resume_id: Optional MCP resume chain ID

        Returns:
            AgentResult with execution outcome

        Note:
            This is a placeholder implementation. Actual integration requires
            Claude Code Task() API which is not directly callable from Python.
            Real implementation will delegate via subprocess or API call.
        """
        task = AgentTask(agent, phase_id, prompt, model, resume_id)
        task_key = f"{phase_id}-{agent}"

        self.active_tasks[task_key] = task

        start_time = time.time()
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # PLACEHOLDER: Actual Task() delegation
                # In real implementation, this would call:
                #   Task(subagent_type=agent, prompt=prompt, model=model, resume=resume_id)
                #
                # For now, simulate successful execution
                result_data = await self._simulate_agent_execution(task)

                # Successful execution
                execution_time = time.time() - start_time

                result = AgentResult(
                    agent=agent,
                    phase_id=phase_id,
                    status=AgentStatus.COMPLETED,
                    execution_time=execution_time,
                    result=result_data,
                    retry_count=retry_count
                )

                self.results_cache[task_key] = result
                del self.active_tasks[task_key]

                return result

            except Exception as e:
                retry_count += 1

                if retry_count > self.max_retries:
                    # Max retries exceeded - fail
                    execution_time = time.time() - start_time

                    result = AgentResult(
                        agent=agent,
                        phase_id=phase_id,
                        status=AgentStatus.FAILED,
                        execution_time=execution_time,
                        error=str(e),
                        retry_count=retry_count - 1
                    )

                    self.results_cache[task_key] = result
                    del self.active_tasks[task_key]

                    return result

                # Retry with exponential backoff
                delay = self.retry_delay * (2 ** (retry_count - 1))
                await asyncio.sleep(delay)

        # Should not reach here, but handle edge case
        execution_time = time.time() - start_time
        result = AgentResult(
            agent=agent,
            phase_id=phase_id,
            status=AgentStatus.FAILED,
            execution_time=execution_time,
            error="Unknown error - max retries exceeded",
            retry_count=retry_count
        )

        self.results_cache[task_key] = result
        return result

    async def execute_parallel(
        self,
        tasks: list[AgentTask],
        max_concurrent: int = 5
    ) -> list[AgentResult]:
        """
        Execute multiple agents in parallel with concurrency limit

        Args:
            tasks: List of AgentTask to execute
            max_concurrent: Maximum concurrent agents

        Returns:
            List of AgentResult (same order as input tasks)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task: AgentTask) -> AgentResult:
            async with semaphore:
                return await self.execute_agent(
                    agent=task.agent,
                    phase_id=task.phase_id,
                    prompt=task.prompt,
                    model=task.model,
                    resume_id=task.resume_id
                )

        # Execute all tasks concurrently (up to max_concurrent at a time)
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # Convert exceptions to failed AgentResults
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    AgentResult(
                        agent=tasks[i].agent,
                        phase_id=tasks[i].phase_id,
                        status=AgentStatus.FAILED,
                        execution_time=0.0,
                        error=str(result)
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def execute_phase(
        self,
        phase_id: int,
        agents: list[str],
        prompt_template: str,
        mode: Literal["sequential", "parallel"],
        max_parallel: int = 5
    ) -> PhaseResult:
        """
        Execute a complete workflow phase

        Args:
            phase_id: Phase number
            agents: List of agent identifiers
            prompt_template: Prompt template (same for all agents in phase)
            mode: "sequential" or "parallel"
            max_parallel: Max concurrent agents (parallel mode only)

        Returns:
            PhaseResult with all agent outcomes
        """
        start_time = time.time()

        if mode == "sequential":
            # Execute agents one by one
            results = []
            for agent in agents:
                result = await self.execute_agent(
                    agent=agent,
                    phase_id=phase_id,
                    prompt=prompt_template
                )
                results.append(result)

                # Stop if agent failed (sequential dependency)
                if result.status == AgentStatus.FAILED:
                    break

        else:  # parallel
            # Execute agents concurrently
            tasks = [
                AgentTask(agent, phase_id, prompt_template)
                for agent in agents
            ]
            results = await self.execute_parallel(tasks, max_concurrent=max_parallel)

        execution_time = time.time() - start_time

        # Determine phase status
        failed_results = [r for r in results if r.status == AgentStatus.FAILED]
        completed_results = [r for r in results if r.status == AgentStatus.COMPLETED]

        if len(failed_results) == 0:
            status = "completed"
        elif len(completed_results) == 0:
            status = "failed"
        else:
            status = "partial"

        errors = [r.error for r in failed_results if r.error]

        return PhaseResult(
            phase_id=phase_id,
            status=status,
            agent_results=results,
            execution_time=execution_time,
            errors=errors
        )

    async def _simulate_agent_execution(self, task: AgentTask) -> dict[str, Any]:
        """
        PLACEHOLDER: Simulate agent execution for testing

        Real implementation will delegate via Task() API

        Args:
            task: AgentTask to execute

        Returns:
            Simulated result data
        """
        # Simulate execution time
        await asyncio.sleep(0.1)

        return {
            "agent": task.agent,
            "phase": task.phase_id,
            "status": "completed",
            "files_modified": [],
            "message": f"Agent {task.agent} completed phase {task.phase_id}"
        }

    def get_phase_summary(self, phase_id: int) -> Optional[dict[str, Any]]:
        """
        Get summary of all agents executed in a phase

        Args:
            phase_id: Phase number

        Returns:
            Summary dict with agent counts and statuses
        """
        phase_results = [
            r for k, r in self.results_cache.items()
            if r.phase_id == phase_id
        ]

        if not phase_results:
            return None

        return {
            "phase_id": phase_id,
            "total_agents": len(phase_results),
            "completed": len([r for r in phase_results if r.status == AgentStatus.COMPLETED]),
            "failed": len([r for r in phase_results if r.status == AgentStatus.FAILED]),
            "total_time": sum(r.execution_time for r in phase_results),
            "avg_time": sum(r.execution_time for r in phase_results) / len(phase_results)
        }

    def clear_cache(self):
        """Clear results cache"""
        self.results_cache.clear()


# Module-level convenience function
def create_coordinator(max_retries: int = 2) -> AgentCoordinator:
    """
    Create an AgentCoordinator with default or custom settings

    Args:
        max_retries: Maximum retry attempts (default: 2)

    Returns:
        Configured AgentCoordinator instance

    Example:
        coordinator = create_coordinator(max_retries=3)
        result = await coordinator.execute_agent(
            agent="expert-backend",
            phase_id=1,
            prompt="Implement authentication"
        )
    """
    return AgentCoordinator(max_retries=max_retries)
