"""
Epistemic Feeling Interpreter: Translates objective state into subjective feeling.
"""

import json
from typing import Any, Dict, Optional
from agi.brain import GenAIBrain, TaskType
from agi.world.metaphysical.state import WorldState

class FeelingAdapter:
    """
    Subjective interpretation layer using LLM.
    Acts as the 'nervous system' translating binary state into 'feeling'.
    """
    
    def __init__(self, brain: GenAIBrain):
        self.brain = brain
        
    async def interpret(self, state_before: WorldState, state_after: WorldState, description: str) -> Dict[str, Any]:
        """
        Interprets the transition from S to S' into a Feeling object.
        """
        
        # 1. Prepare textual description of the delta
        prompt = f"""
        TASK: Translate an objective world-state transition into a subjective AGI 'feeling'.
        
        SITUATION: {description}
        
        OBJECTIVE CHANGES:
        - Resources Before: {self._res_to_str(state_before)}
        - Resources After: {self._res_to_str(state_after)}
        - New Entities: {[e.id for e in state_after.entities.values() if e.id not in state_before.entities]}
        
        INSTRUCTIONS:
        1. Analyze how this change affects the AGI's 'well-being' and goals.
        2. Output a JSON object following the Feeling schema.
        3. Include valence (-1 to 1), arousal (0 to 1), intensity, and a concise narrative interpretation.
        
        Output ONLY the JSON.
        """
        
        provider, model = self.brain.select_model(TaskType.FAST)
        client = self.brain.get_client(provider)
        
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are the 'Sentience Module' of an AGI. You interpret objective data into subjective emotional and cognitive states."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"} if provider == "openai" else None
            )
            
            text = resp.choices[0].message.content
            # Basic cleanup if not using json_object mode
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text)
        except Exception as e:
            return {
                "valence": 0,
                "arousal": 0,
                "categories": ["confusion"],
                "interpretation": f"Error in nervous system: {str(e)}"
            }

    def _res_to_str(self, state: WorldState) -> str:
        return ", ".join([f"{r.name}: {r.value}" for r in state.resources.values()])
