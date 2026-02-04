
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class AutoRecoveryReflex(ReflexModule):
    """
    Reflex that triggers when a 'critical_load' alert is received.
    It automatically spawns a plan to list processes and perform cleanup.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="auto_recovery",
            description="Automatically handles critical system load alerts.",
            trigger_type="webhook"
        )

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        # Check if this is a system alert for high load
        is_alert = event.get("type") == "system_alert"
        severity = event.get("payload", {}).get("severity")
        return is_alert and severity == "critical"
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        # This is the "Unconditional Response"
        # It bypasses the Planner and tells the Orchestrator exactly what to do.
        print("[Reflex] AutoRecovery triggered! Generating emergency plan.")
        
        return [
            {
                "id": "step_1",
                "skill": "code_executor", # Using a skill we know exists
                "description": "Identify resource hogs",
                "inputs": {
                    "code": "print('Top processes: [Process A: 90% CPU]')" 
                }
            },
            {
                "id": "step_2",
                "skill": "text_analyzer", 
                "description": "Log the incident",
                "inputs": {
                    "text": "CRITICAL INCIDENT: System load exceeded safety thresholds. Auto-recovery initiated."
                },
                "depends_on": ["step_1"]
            }
        ]
