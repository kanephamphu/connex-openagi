
import time
import asyncio
from typing import Any, Dict, List, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class EmotionPerception(PerceptionModule):
    """
    Detects human and AGI emotions in parallel using sub-brains.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="emotion",
            description="Detects emotional state of user and AGI.",
            category="social",
            sub_category="emotional_intelligence",
            version="1.0.0"
        )
        
    def __init__(self, config, sub_brain_manager=None):
        super().__init__(config)
        self.sub_brain = sub_brain_manager
        self.current_state = {
            "human_emotion": "neutral",
            "agi_emotion": "neutral",
            "last_update": 0
        }

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze emotions based on the recent interaction or retrieve from memory.
        """
        memory = getattr(self.config, 'memory_manager', None)
        
        if not self.sub_brain or not query:
            if memory:
                return {**memory.emotional_state, "last_update": self.current_state["last_update"]}
            return self.current_state

        # Prepare parallel tasks for sub-brains
        tasks = [
            {
                "system": "You are an emotion detection specialist. Analyze the HUMAN's query and respond with one word: [happy, sad, angry, neutral, curious, frustrated].",
                "prompt": f"Query: \"{query}\""
            },
            {
                "system": "You are an introspection specialist. Analyze how an AGI should feel about this request and respond with one word: [helpful, concerned, analytical, cautious, enthusiastic].",
                "prompt": f"Request: \"{query}\""
            }
        ]

        try:
            results = await self.sub_brain.execute_parallel(tasks)
            if len(results) >= 2:
                self.current_state["human_emotion"] = results[0].lower()
                self.current_state["agi_emotion"] = results[1].lower()
                self.current_state["last_update"] = time.time()
                
                # Sync back to memory for other modules to use
                if memory:
                    memory.update_emotional_state(self.current_state["human_emotion"], self.current_state["agi_emotion"])
        except Exception as e:
            if self.config.verbose:
                print(f"[EmotionPerception] Detection failed: {e}")

        return self.current_state
