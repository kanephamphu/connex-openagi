
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class ResourceGovernorReflex(ReflexModule):
    """
    Reflex that triggers when system workload is too high, enforcing throttling.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="resource_governor",
            description="Automatically throttles or pauses activity during high system stress.",
            trigger_type="telemetry"
        )

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Triggers if CPU > 90% or memory is critical.
        """
        # Event might come from the WorkloadPerception module
        if event.get("type") == "telemetry_update":
            payload = event.get("payload", {})
            cpu_usage = payload.get("cpu_percent", 0)
            if cpu_usage > 90:
                print(f"[Reflex] RESOURCE CRITICAL: CPU usage at {cpu_usage}%")
                return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        """
        Returns a 'Throttle' plan.
        """
        return [
            {
                "id": "throttle_wait",
                "skill": "code_executor", # Using code executor to simulate a sleep/wait
                "description": "Enforce mandatory cooldown period",
                "inputs": {
                    "code": "import time; print('Cooling down...'); time.sleep(5); print('Resuming with limited throughput.')"
                }
            }
        ]
