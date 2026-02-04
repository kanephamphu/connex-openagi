
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ReflexMetadata:
    name: str
    description: str
    trigger_type: str # e.g. "webhook", "event", "schedule"
    version: str = "0.1.0"
    config_schema: Optional[Dict[str, Any]] = None

class ReflexModule(ABC):
    """
    Base class for a Reflex Module.
    Reflexes are automatic "If Trigger -> Then Plan" units.
    They run largely independent of the main deliberative planner until triggered.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active = True

    @property
    @abstractmethod
    def metadata(self) -> ReflexMetadata:
        pass

    @abstractmethod
    async def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Check if the incoming event triggers this reflex.
        """
        pass
        
    @abstractmethod
    async def get_plan(self) -> List[Dict[str, Any]]:
        """
        Return the execution plan (DAG or sequence of actions) when triggered.
        """
        pass
