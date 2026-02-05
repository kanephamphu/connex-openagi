
from typing import Any, Dict, Optional
from agi.skilldock.base import Skill, SkillMetadata
import asyncio

class EmotionDetectionSkill(Skill):
    """
    Skill to detect human and AGI emotions using sub-brains and update memory.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="emotion_detection",
            description="Analyzes text to detect human and AGI emotional states.",
            version="1.0.0",
            category="social",
            usage="detect_emotion(text='user input')"
        )

    def __init__(self, config):
        super().__init__(config)
        self.sub_brain = getattr(config, 'sub_brain_manager', None)

    async def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        if not self.sub_brain:
            return {"success": False, "error": "Sub-brain manager not configured."}

        # Prepare parallel tasks for sub-brains
        tasks = [
            {
                "system": "You are an emotion detection specialist. Analyze the HUMAN's query and respond with one word: [happy, sad, angry, neutral, curious, frustrated].",
                "prompt": f"Query: \"{text}\""
            },
            {
                "system": "You are an introspection specialist. Analyze how an AGI should feel about this request and respond with one word: [helpful, concerned, analytical, cautious, enthusiastic].",
                "prompt": f"Request: \"{text}\""
            }
        ]

        try:
            results = await self.sub_brain.execute_parallel(tasks)
            if len(results) >= 2:
                human_emotion = results[0].lower()
                agi_emotion = results[1].lower()
                
                # Update Memory (this assumes we have access to context or it's handled globally)
                # In our architecture, the Skill should ideally return values and the Orchestrator/Memory should handle updates,
                # but for this specific "infrastructure" request, we'll try to find the memory manager if attached to config.
                memory = getattr(self.config, 'memory_manager', None)
                if memory:
                    memory.update_emotional_state(human_emotion, agi_emotion)

                return {
                    "success": True,
                    "human_emotion": human_emotion,
                    "agi_emotion": agi_emotion
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Incomplete results from sub-brains."}
