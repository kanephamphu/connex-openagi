
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class HealthcareReflex(ReflexModule):
    """
    Handles healthcare-check type time events.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="healthcare_handler",
            description="Handles health care reminders and check-ins.",
            trigger_type="time_event"
        )
        
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "time_event":
            payload = event.get("payload", {})
            return payload.get("event_type") == "healthcare_check"
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "healthcare_reminder",
                "skill": "speak",
                "description": "Provide healthcare reminder",
                "inputs": {
                    "text": "It's time for your health care check-in. Staying on schedule is important for your well-being."
                },
                "depends_on": []
            }
        ]
