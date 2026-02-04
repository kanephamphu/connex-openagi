
import requests
from typing import Any, Dict, List, Optional
from agi.skilldock.base import Skill, SkillMetadata

class WeatherSkill(Skill):
    """
    Skill for fetching weather data using Open-Meteo API.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="weather",
            description="Checks current weather for a city.",
            category="web",
            sub_category="data",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Name of the city (e.g., 'London')"}
                },
                "required": ["location"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "condition": {"type": "string"},
                    "wind_speed": {"type": "number"},
                    "location": {"type": "string"}
                }
            }
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        location_input = kwargs.get("location") or kwargs.get("city")
        if not location_input:
            return {"success": False, "message": "Location/City name is required"}
            
        # 1. Geocode
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_input}&count=1&language=en&format=json"
            geo_resp = requests.get(geo_url, timeout=5)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            
            if not geo_data.get("results"):
                return {"error": f"City '{city}' not found."}
                
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            
            # 2. Weather
            # Using current_weather=true
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            w_resp = requests.get(w_url, timeout=5)
            w_resp.raise_for_status()
            w_data = w_resp.json()
            
            current = w_data.get("current_weather", {})
            
            return {
                "success": True,
                "location": name,
                "temperature": current.get("temperature"),
                "wind_speed": current.get("windspeed"),
                "condition": f"Weather Code: {current.get('weathercode')}",
                "status": "success"
            }
            
        except Exception as e:
            return {"error": f"Weather fetch failed: {str(e)}"}
