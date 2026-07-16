"""
MoAI-ADK Workflow Execution Engine

Provides workflow orchestration with:
- DAG-based phase execution
- Parallel agent coordination
- Dynamic resource monitoring
- MCP resume chain integration

Components:
- executor: Main orchestration loop
- coordinator: Agent delegation and result collection
- resource_monitor: Dynamic parallelism adjustment
"""

__version__ = "1.0.0"
__all__ = ["executor", "coordinator", "resource_monitor"]
