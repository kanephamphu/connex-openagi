"""
World Manager: Orchestrates the objective reality and subjective experience.
"""

from typing import Any, Dict, List, Optional, Tuple
from agi.config import AGIConfig
from agi.brain import GenAIBrain
from agi.world.metaphysical.state import WorldState, Resource
from agi.world.metaphysical.action import Action
from agi.world.metaphysical.causality_engine import CausalityEngine
from agi.world.epistemic.feeling.llm_adapter import FeelingAdapter

class WorldManager:
    """
    Unified interface for the AGI's world consciousness.
    """
    def __init__(self, config: AGIConfig, brain: GenAIBrain):
        self.config = config
        from agi.sub_brain import SubBrainManager
        self.sub_brain_manager = SubBrainManager(config)
        self.causality = CausalityEngine(model_path="world_model.pth")
        self.feeling_adapter = FeelingAdapter(brain)
        
        # Initialize default world state
        self.state = WorldState()
        self._setup_initial_resources()

    def _setup_initial_resources(self):
        """Initial bootstrap of the world's measured values."""
        self.state.resources["storage"] = Resource("storage", 1000, "MB")
        self.state.resources["api_credits"] = Resource("api_credits", 100, "units")
        self.state.resources["time"] = Resource("time", 0, "s")
        self.state.resources["health"] = Resource("health", 100, "%")

    async def step(self, action_type: str, params: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Execute a world-step:
        1. Predict objective change.
        2. Update objective state.
        3. Interpret subjective feeling.
        """
        action = Action(agent="agi", type=action_type, params=params, description=description)
        
        # 1. Metaphysical Transition (Neural + Guard)
        next_state, error = await self.causality.predict(self.state, action)
        
        if error:
            return {
                "success": False,
                "error": error,
                "feeling": {
                    "valence": -0.5,
                    "arousal": 0.3,
                    "categories": ["blocked"],
                    "interpretation": f"Objective limitation encountered: {error}"
                }
            }
            
        # 2. Epistemic Interpretation (Subjective)
        feeling = await self.feeling_adapter.interpret(self.state, next_state, description)
        
        # 3. Commit state change
        old_state = self.state
        self.state = next_state
        
        return {
            "success": True,
            "old_state": old_state,
            "new_state": next_state,
            "feeling": feeling
        }

    async def simulate_consequence(self, action_type: str, params: Dict[str, Any], description: str) -> Tuple[bool, Optional[str]]:
        """Neural causal check without committing state."""
        action = Action(agent="agi", type=action_type, params=params, description=description)
        return await self.causality.simulate(self.state, action)

    def train_from_experience(self, old_state: WorldState, action_type: str, params: Dict[str, Any], result_state: WorldState):
        """Improve the world model based on historical data."""
        action = Action(agent="agi", type=action_type, params=params)
        loss = self.causality.train_step(old_state, action, result_state)
        return loss

    def save_knowledge(self):
        """Persist the learned world cognition."""
        self.causality.save_weights()
