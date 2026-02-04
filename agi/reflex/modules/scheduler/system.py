
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class SchedulerReflex(ReflexModule):
    """
    Acts on time ticks.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="scheduler",
            description="Triggers periodic tasks.",
            trigger_type="tick"
        )
        
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "tick":
            # For demo, just always say yes to verify "alive"
            # Real version would check a schedule db
            payload = event.get("payload", {})
            # print(f"[Reflex] Scheduler Tick: {payload.get('readable')}")
            # Don't trigger every tick to avoid spam, maybe trigger every minute?
            # Hack: trigger if seconds is roughly 00 (handled by perception spacing mostly)
            return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        # Just a heartbeat log
        return [
             # No-op action, or effectively a log
             # Returning empty plan could mean no action but reflex triggered.
        ]
