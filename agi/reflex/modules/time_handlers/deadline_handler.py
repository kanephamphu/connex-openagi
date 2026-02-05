
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class DeadlineReflex(ReflexModule):
    """
    Handles deadline-type time events.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="deadline_handler",
            description="Alerts for approaching deadlines.",
            trigger_type="time_event"
        )
        
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "time_event":
            payload = event.get("payload", {})
            return payload.get("event_type") == "deadline"
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "deadline_alert",
                "skill": "speak",
                "description": "Announce deadline alert",
                "inputs": {
                    "text": "Warning: A deadline is being reached now. Please check your tasks."
                },
                "depends_on": []
            }
        ]
