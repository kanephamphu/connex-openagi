"""
Tier 1: The Planner (Architect)

Decomposes user goals into structured action sequences using high-reasoning models.
"""

from agi.planner.base import ActionNode, ActionPlan, PlannerResult, Planner as AbstractPlanner
from agi.planner.brain_planner import BrainPlanner

# Export BrainPlanner as the default Planner implementation alias
Planner = BrainPlanner

__all__ = ["Planner", "BrainPlanner", "AbstractPlanner", "ActionNode", "ActionPlan", "PlannerResult"]
