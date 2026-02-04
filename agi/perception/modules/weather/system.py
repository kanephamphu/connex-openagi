
import asyncio
import time
from typing import Any, Dict, Optional
import requests
from agi.perception.base import PerceptionModule, PerceptionMetadata

class WeatherPerception(PerceptionModule):
    """
    Passive weather monitoring for a fixed location.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="weather_monitor",
            description="Monitors local weather conditions.",
            category="environment",
            sub_category="data",
            version="1.0.0"
        )
        
    def __init__(self, config):
        super().__init__(config)
        # Default to San Francisco if not configured
        self.lat = 37.7749
        self.lon = -122.4194
        self.last_check = 0
        self.last_code = None # storing weather code to detect change
        self.check_interval = 60 # Check every 60s for demo purposes (real: 30m)

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        On-demand check.
        """
        return self._fetch_weather()
    
    def _fetch_weather(self) -> Dict[str, Any]:
        try:
             w_url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current_weather=true"
             resp = requests.get(w_url, timeout=5)
             if resp.status_code == 200:
                 return resp.json().get("current_weather", {})
        except:
            pass
        return {}

    async def check_conditions(self) -> Optional[Dict[str, Any]]:
        """
        Active polling method.
        """
        now = time.time()
        if now - self.last_check > self.check_interval:
            self.last_check = now
            current = self._fetch_weather()
            current_code = current.get("weathercode")
            
            if current_code is not None:
                # If code changed, emit event
                if self.last_code is not None and current_code != self.last_code:
                    old_code = self.last_code
                    self.last_code = current_code
                    return {
                        "type": "weather_change",
                        "payload": {
                            "old_code": old_code,
                            "new_code": current_code,
                            "temp": current.get("temperature")
                        }
                    }
                elif self.last_code is None:
                    # First initialization
                    self.last_code = current_code
                    
        return None
