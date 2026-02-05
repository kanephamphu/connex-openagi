
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
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Analyzing deep emotional sentiment [happy, sad, angry, neutral, curious, frustrated, anxious, grateful, bored, excited]"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "human_emotion": {"type": "string", "description": "Detected human sentiment"},
                    "agi_emotion": {"type": "string", "description": "Introspected AGI state [helpful, concerned, analytical, cautious, enthusiastic, apologetic, determined, playful]"},
                    "success": {"type": "boolean"}
                }
            }
        )

    def __init__(self, config):
        super().__init__(config)

    async def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        # Dynamically retrieve sub_brain from agi_config to handle async initialization
        sub_brain = getattr(self.agi_config, 'sub_brain_manager', None)
        if not sub_brain:
            return {"success": False, "error": "Sub-brain manager not configured."}
            
        tasks = [
            {
                "system": (
                    "You are an Expert Empathy Analyst. Analyze the HUMAN's query deeply.\n"
                    "Determine the primary emotional state based on tone, keywords, and punctuation.\n"
                    "Categories: [happy, sad, angry, neutral, curious, frustrated, anxious, grateful, bored, excited].\n"
                    "Respond with EXACTLY one word from the list."
                ),
                "prompt": f"User Query: \"{text}\"\nDetected Emotion:"
            },
            {
                "system": (
                    "You are a Self-Aware Artificial Intelligence. Introspect and determine how you should feel\n"
                    "internally when handling this specific request to be most effective and empathetic.\n"
                    "States: [helpful, concerned, analytical, cautious, enthusiastic, apologetic, determined, playful].\n"
                    "Respond with EXACTLY one word from the list."
                ),
                "prompt": f"Goal/Request: \"{text}\"\nInternal State:"
            }
        ]

        try:
            results = await sub_brain.execute_parallel(tasks)
            if len(results) >= 2:
                human_emotion = results[0].strip().lower().strip("[]().")
                agi_emotion = results[1].strip().lower().strip("[]().")
                
                # Update Memory
                memory = getattr(self.agi_config, 'memory_manager', None)
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
