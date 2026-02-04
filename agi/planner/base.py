"""
Base classes and types for the Planner tier.

Defines the core abstractions for action planning and decomposition.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
import networkx as nx


class ActionNode(BaseModel):
    """
    Represents a single action in the plan.
    
    Each action is a discrete step that can be executed by a skill.
    """
    
    id: str = Field(description="Unique identifier for this action")
    skill: str = Field(description="Name of the skill to execute")
    description: str = Field(description="Human-readable description of what this action does")
    
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for this action"
    )
    input_schema: Dict[str, str] = Field(
        default_factory=dict,
        description="Expected input types (e.g., {'urls': 'List[str]'})"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected output types (e.g., {'results': 'List[dict]' or JSON schema})"
    )
    
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of actions that must complete before this one"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (timeout, retries, etc.)"
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return self.model_dump()


class ActionPlan(BaseModel):
    """
    A directed acyclic graph (DAG) of actions to accomplish a goal.
    
    The plan ensures proper ordering and dependency management.
    """
    
    goal: str = Field(description="The original user goal")
    actions: List[ActionNode] = Field(description="All actions in the plan")
    reasoning: str = Field(
        default="",
        description="Chain-of-thought reasoning used to create this plan"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plan-level metadata"
    )
    
    def __post_init__(self):
        """Validate the plan structure."""
        self._validate_dag()
    
    def _validate_dag(self):
        """
        Ensure the plan forms a valid DAG with no cycles.
        
        Raises:
            ValueError: If the plan contains cycles or invalid dependencies
        """
        # Build graph
        G = nx.DiGraph()
        for action in self.actions:
            G.add_node(action.id)
            for dep in action.depends_on:
                G.add_edge(dep, action.id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(G):
            cycles = list(nx.simple_cycles(G))
            raise ValueError(f"Plan contains cycles: {cycles}")
        
        # Check all dependencies exist
        action_ids = {a.id for a in self.actions}
        for action in self.actions:
            for dep in action.depends_on:
                if dep not in action_ids:
                    raise ValueError(
                        f"Action {action.id} depends on non-existent action {dep}"
                    )
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get the topological ordering of actions for execution.
        
        Returns:
            List of levels, where each level contains action IDs that can run in parallel
        """
        G = nx.DiGraph()
        for action in self.actions:
            G.add_node(action.id)
            for dep in action.depends_on:
                G.add_edge(dep, action.id)
        
        # Get topological generations (levels that can run in parallel)
        levels = list(nx.topological_generations(G))
        return levels
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "goal": self.goal,
            "actions": [a.to_dict() for a in self.actions],
            "reasoning": self.reasoning,
            "execution_order": self.get_execution_order(),
            "metadata": self.metadata,
        }


@dataclass
class PlannerResult:
    """Result from the planning phase."""
    
    plan: ActionPlan
    success: bool = True
    error: Optional[str] = None
    reasoning_tokens: int = 0
    planning_time: float = 0.0


class Planner(ABC):
    """
    Abstract base class for planners.
    
    Planners decompose user goals into executable action sequences.
    """
    
    def __init__(self, config):
        """
        Initialize the planner.
        
        Args:
            config: AGIConfig instance
        """
        self.config = config
        self.client = config.get_planner_client()
    
    @abstractmethod
    async def create_plan(self, goal: str, context: dict) -> ActionPlan:
        """
        Create an action plan from a user goal.
        
        Args:
            goal: Natural language description of what to accomplish
            context: Additional context and constraints
            
        Returns:
            ActionPlan with structured action sequence
        """
        pass
    
    async def create_plan_streaming(self, goal: str, context: dict):
        """
        Create a plan with streaming of reasoning process.
        
        Args:
            goal: Natural language description of what to accomplish
            context: Additional context and constraints
            
        Yields:
            Progress updates including reasoning steps and partial plans
        """
        # Default implementation: create plan and yield final result
        plan = await self.create_plan(goal, context)
        yield {
            "type": "plan_complete",
            "plan": plan,
        }
    
    async def replan(
        self,
        original_plan: ActionPlan,
        failed_step: str,
        error: str,
        completed_steps: List[str]
    ) -> ActionPlan:
        """
        Re-plan remaining actions after a failure.
        
        Args:
            original_plan: The original plan that failed
            failed_step: ID of the action that failed
            error: Error message from the failure
            completed_steps: IDs of successfully completed actions
            
        Returns:
            New ActionPlan for remaining work
        """
        # Build context for re-planning
        replan_context = {
            "original_goal": original_plan.goal,
            "completed_actions": completed_steps,
            "failed_action": failed_step,
            "error": error,
            "remaining_actions": [
                a.id for a in original_plan.actions
                if a.id not in completed_steps and a.id != failed_step
            ]
        }
        
        # Create new plan
        new_goal = f"Continue working on: {original_plan.goal}\n"
        new_goal += f"Previous attempt failed at step '{failed_step}' with error: {error}\n"
        new_goal += f"Completed steps: {', '.join(completed_steps)}"
        
        return await self.create_plan(new_goal, replan_context)
