from agi.skilldock.base import Skill, SkillMetadata
from typing import Dict, Any
import asyncio

class AGIInterfaceSkill(Skill):
    """
    Bridge skill that allows aspects of the AGI (like Reflexes) to 
    submit new goals to the core Brain for execution.
    """
    def __init__(self, config, agi_execute_callback=None):
        super().__init__(config)
        self.agi_execute_callback = agi_execute_callback

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="agi_brain_interface",
            description="Internal interface to submit new goals to the AGI brain.",
            category="system",
            sub_category="bridge",
            input_schema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The natural language goal/command to process"},
                    "speak": {"type": "boolean", "description": "Whether to vocalize the final result", "default": True}
                },
                "required": ["goal"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": "string",
                    "message": "string"
                }
            }
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        goal = kwargs.get("goal")
        speak = kwargs.get("speak", True)
        if not goal:
            return {"error": "Goal required"}
        
        # Fire and forget: we don't want the reflex execution to block 
        # on the entire goal decomposition and execution.
        def task_done_callback(t):
            try:
                t.result()
            except Exception as e:
                print(f"[AGIInterfaceSkill] Error executing delegated goal: {e}")

        task = asyncio.create_task(self.agi_execute_callback(goal, speak_output=speak))
        task.add_done_callback(task_done_callback)
        
        return {"status": "submitted", "goal": goal}
