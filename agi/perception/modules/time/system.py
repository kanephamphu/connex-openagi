
import asyncio
import time
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class TimePerception(PerceptionModule):
    """
    Senses time progression and emits tick events.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="time_sense",
            description="Provides time awareness and tick events.",
            version="1.0.0"
        )
        
    def __init__(self, config):
        super().__init__(config)
        self.last_tick = 0

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {"timestamp": time.time(), "human_readable": time.ctime()}
    
    async def check_ticks(self) -> Optional[Dict[str, Any]]:
        """
        Called periodically to generate time events.
        """
        current_time = time.time()
        # Report every 10 seconds for demo (or minute usually)
        if current_time - self.last_tick > 10:
            self.last_tick = current_time
            return {
                "type": "tick",
                "payload": {"timestamp": current_time, "readable": time.ctime()}
            }
        return None
