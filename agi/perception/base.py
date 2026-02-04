
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

@dataclass
class PerceptionMetadata:
    name: str
    description: str
    category: str = "general"
    sub_category: str = "general"
    version: str = "0.1.0"
    config_schema: Optional[Dict[str, Any]] = None

class PerceptionModule(ABC):
    """
    Base class for a Perception Module.
    Perception modules gather data from the environment (Real world, Digital environment, etc.)
    and normalize it for the AGI.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connected = False

    @property
    @abstractmethod
    def metadata(self) -> PerceptionMetadata:
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the perception source (e.g. MCP Server)."""
        pass

    @abstractmethod
    async def perceive(self, query: Optional[str] = None, **kwargs) -> Any:
        """
        Gather perception data.
        
        Args:
            query: Focus/Filter for perception (e.g., "Look for red objects")
            **kwargs: Extra parameters
            
        Returns:
            Normalized data structure
        """
        pass

    async def disconnect(self):
        """Clean up resources."""
        pass
