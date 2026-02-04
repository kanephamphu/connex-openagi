
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class SelfRepairReflex(ReflexModule):
    """
    Reflex that monitors system health/history for repeated failures and triggers self-repair.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="auto_healer",
            description="Detects high error rates and triggers generic diagnostics.",
            trigger_type="history_check" # Not a real type, we simulate it
        )
        
    def __init__(self, config, history_manager=None):
        super().__init__(config)
        self.history_manager = history_manager
        self.failure_threshold = 3

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Check if the 'event' is an error notification OR scan history.
        """
        # Scenario 1: Event is an error report
        if event.get("type") == "execution_error":
             # We could check if this is the Nth error
             return True
             
        # Scenario 2: Active scan (e.g. heartbeat).
        # We'll assume the system sends a 'health_check' event periodically
        if event.get("type") == "health_check" and self.history_manager:
            # Check recent history
            # Assuming history_manager has get_recent()
            recent = self.history_manager.get_recent(limit=self.failure_threshold)
            
            # Count failures (naive check)
            failures = 0
            for item in recent:
                 if item.get("status") == "failed" or "error" in str(item).lower():
                     failures += 1
            
            if failures >= self.failure_threshold:
                print(f"[Reflex] SELF-REPAIR: Detected {failures} recent failures.")
                return True
                
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        """
        Returns a 'Diagnostics' plan.
        """
        return [
            {
                "id": "run_diagnostics",
                "skill": "system_monitor", # Or we use code execution
                "description": "Run system health check due to high error rate.",
                "inputs": {
                    "query": "full_report"
                }
            },
            {
                "id": "announce_repair",
                "skill": "speak",
                "description": "Announce repair mode",
                "inputs": {
                    "text": "Warning: High error rate detected. Initiating self-diagnostic sequence."
                }
            }
        ]
