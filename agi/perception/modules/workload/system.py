
import psutil
import time
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class WorkloadPerception(PerceptionModule):
    """
    Senses real-world hardware telemetry and internal AGI workload metrics.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="workload_monitor",
            description="Perceives CPU, memory usage, and internal task pressure.",
            category="core",
            sub_category="state",
            version="1.0.0"
        )

    async def connect(self) -> bool:
        self.connected = True
        return True

    def __init__(self, config, identity_manager=None):
        super().__init__(config)
        self.config = config
        self.identity_manager = identity_manager

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Returns snapshot of current system load.
        """
        cpu_usage = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        # Update Identity
        if self.identity_manager:
            self.identity_manager.update_health(cpu=cpu_usage, ram=ram)
            
        memory = psutil.virtual_memory()
        
        # In a real system, we'd also check the Orchestrator's queue length here.
        # For now, we simulate internal pressure.
        
        data = {
            "timestamp": time.time(),
            "cpu_percent": cpu_usage,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "status": "nominal" if cpu_usage < 70 else "stressed" if cpu_usage < 90 else "critical"
        }
        
        return data
