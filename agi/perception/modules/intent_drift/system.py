
from typing import Any, Dict, Optional, List
from agi.perception.base import PerceptionModule, PerceptionMetadata

class IntentDriftPerception(PerceptionModule):
    """
    Senses shifts in user intent by comparing current goal with short-term history.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="intent_drift",
            description="Detects if the user's current request diverges from the ongoing task sequence.",
            category="core",
            sub_category="cognition",
            version="1.0.0"
        )

    def __init__(self, config, memory_manager=None):
        super().__init__(config)
        self.memory_manager = memory_manager

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Calculates drift score based on current goal vs ST context.
        """
        current_goal = query or kwargs.get("goal", "")
        if not self.memory_manager or not current_goal:
            return {"drift_score": 0.0, "status": "unknown"}
            
        recent_context = self.memory_manager.short_term
        if not recent_context:
            return {"drift_score": 0.0, "status": "fresh_session"}
            
        # Drift detection logic (Simplified/Mock for foundation)
        # In production, we'd use semantic similarity between goals.
        last_goal = recent_context[-1].get("goal", "")
        
        # Very simple keyword-based drift detection for demo
        last_keywords = set(last_goal.lower().split())
        current_keywords = set(current_goal.lower().split())
        overlap = len(last_keywords.intersection(current_keywords))
        
        drift_score = 1.0 - (overlap / max(len(last_keywords), 1))
        
        return {
            "current_goal": current_goal,
            "last_goal": last_goal,
            "drift_score": round(drift_score, 2),
            "status": "stable" if drift_score < 0.5 else "drifting"
        }
