
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class CalendarReflex(ReflexModule):
    """
    Handles calendar-type time events.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="calendar_handler",
            description="Handles calendar-related notifications and actions.",
            trigger_type="time_event"
        )
        
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "time_event":
            payload = event.get("payload", {})
            return payload.get("event_type") == "calendar"
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "calendar_notice",
                "skill": "speak",
                "description": "Announce calendar event",
                "inputs": {
                    "text": "Excuse me, I have a calendar reminder for you. It's time for your scheduled event."
                },
                "depends_on": []
            }
        ]
