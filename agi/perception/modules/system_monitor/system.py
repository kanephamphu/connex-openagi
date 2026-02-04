
import random
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class SystemMonitorPerception(PerceptionModule):
    """
    Perceives system health metrics (CPU, Memory, Disk).
    Simulates checking an MCP resource `system://metrics/live`.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="system_monitor",
            description="Provides real-time system metrics (CPU, RAM). Use this to check server health.",
            category="system",
            sub_category="metrics",
            version="1.0.0"
        )

    async def connect(self) -> bool:
        # Simulate connecting to a local agent or MCP server
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Get current system metrics.
        Query can filtered like "cpu_only" or "full_report".
        """
        # Mock data for demonstration
        cpu_usage = random.randint(10, 95)
        memory_usage = random.randint(20, 80)
        
        data = {
            "node": "primary-worker-1",
            "status": "active",
            "metrics": {
                "cpu_percent": cpu_usage,
                "memory_percent": memory_usage,
                "disk_free_gb": 120
            }
        }
        
        # Add semantic context (normalization)
        if cpu_usage > 80:
            data["analysis"] = "CRITICAL_LOAD"
        elif cpu_usage > 60:
            data["analysis"] = "HIGH_LOAD"
        else:
            data["analysis"] = "NORMAL"
            
        return data
