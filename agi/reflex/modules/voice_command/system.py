
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class VoiceCommandReflex(ReflexModule):
    """
    Reflex that reacts to voice input by delegating it to the planner.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="voice_commander",
            description="Transforms spoken text into a goal-oriented plan.",
            trigger_type="voice_input"
        )

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Triggers if the event contains valid spoken text.
        """
        if event.get("type") == "voice_input":
            text = event.get("payload", {}).get("text")
            status = event.get("payload", {}).get("status")
            if status == "success" and text:
                print(f"[Reflex] Voice Command Triggered: '{text}'")
                return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        """
        Returns a plan to 'Execute' the user's spoken command.
        But wait, the Reflex usually returns a plan of *Skills*.
        How do we tell it to "Plan for this goal"?
        
        We can use a special skill or just a 'planner_call'.
        Actually, the Orchestrator executes this plan.
        We probably want a 'meta-skill' that calls the planner, or we define the action.
        
        For now, let's assume we have a way to inject a new goal.
        Or simpler: The reflex plan IS the action to fulfill the command?
        No, the command is unknown.
        
        Better approach: The Reflex returns an action that simply 'acks' the command,
        and maybe we rely on the main loop to pick up the intention?
        
        Alternative: A dedicated 'PlannerSkill' that recursively calls the planer.
        Let's try to simply PRINT for now, and rely on the demo loop to take the text and pass it to AGI.execute().
        
        Wait, the User asked for "reflex is allow to plan the action".
        This implies the Reflex itself should bridge to the Planner.
        
        Let's define a 'plan_delegation' action.
        """
        # We need the text from the event context. 
        # But get_plan doesn't take args in the base class?
        # Let's check base.py... it seems get_plan doesn't take the event.
        # This is a limitation of my current ReflexModule interface.
        # I should probably store the triggering event in 'evaluate' or pass it.
        
        # Hack: self.last_event was set? No.
        # I will assume I need to fix the interface or store state.
        pass 
    
    # Store state for now
    def __init__(self, config):
        super().__init__(config)
        self.last_command = ""

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "voice_input":
            text = event.get("payload", {}).get("text")
            status = event.get("payload", {}).get("status")
            if status == "success" and text:
                self.last_command = text
                print(f"[Reflex] Voice Command Triggered: '{text}'")
                return True
        return False

    async def get_plan(self) -> List[Dict[str, Any]]:
        # Get full conversation context if memory is available
        memory = getattr(self.config, 'memory_manager', None)
        full_conversation = self.last_command
        
        if memory:
            history = memory.conversation_history
            if history:
                conv_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history])
                full_conversation = f"{conv_text}\nUser: {self.last_command}"

        return [
            {
                "id": "detect_emotion",
                "skill": "emotion_detection",
                "description": "Analyzing target human emotions and self emotions in parallel with full conversation context.",
                "inputs": {
                    "text": full_conversation
                },
                "depends_on": []
            },
            {
                "id": "delegate_to_brain",
                "skill": "agi_brain_interface",
                "description": "Delegating spoken command to the AGI brain for decomposition with emotional awareness and full conversation context.",
                "inputs": {
                    "goal": full_conversation,
                    "speak": True
                },
                "depends_on": ["detect_emotion"]
            }
        ]
