
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class WeatherAlertReflex(ReflexModule):
    """
    Alerts on significant weather changes.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="weather_alert",
            description="Notifies user of weather changes.",
            trigger_type="weather_change"
        )
    
    # Simple code mapping for demo
    def _get_condition_text(self, code):
        if code == 0: return "Clear sky"
        if code in [1,2,3]: return "Partly cloudy"
        if code in [45,48]: return "Fog"
        if code in [51,53,55]: return "Drizzle"
        if code in [61,63,65]: return "Rain"
        if code in [71,73,75]: return "Snow"
        if code >= 95: return "Thunderstorm"
        return "Unknown"

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "weather_change":
            # Always trigger on change for demo
            return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        # In a real event, we'd have access to the event payload here via state or argument
        # But ReflexModule.get_plan is parameterless in current design.
        # Implies module needs to store 'context' from evaluate step.
        
        # NOTE: AGI architecture limitation found. 
        # `evaluate` returns bool, `get_plan` is called after. 
        # We should store the event data in `self.latest_event` during evaluate.
        # But `evaluate` is concurrent... assuming sequential processing for same instance.
        
        return [
            {
                "id": "weather_notification",
                "skill": "speak",
                "description": "Announce weather change",
                "inputs": {
                    "text": "Weather alert: Conditions have changed."
                }
            }
        ]

    # Override for state capture
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "weather_change":
            self.latest_weather = event.get("payload", {})
            return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        new_code = self.latest_weather.get("new_code", 0)
        condition = self._get_condition_text(new_code)
        temp = self.latest_weather.get("temp", "N/A")
        
        return [
            {
                "id": "weather_notification",
                "skill": "speak",  # Assuming SpeakSkill exists
                "description": "Announce weather change",
                "inputs": {
                    "text": f"Weather Update: It is now {condition} and {temp} degrees."
                }
            }
        ]
