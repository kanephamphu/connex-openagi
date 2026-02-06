"""
Metaphysical State: Objective representation of the world.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional
from datetime import datetime

@dataclass
class Entity:
    """An objective thing in the world."""
    id: str
    type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)

@dataclass
class Relation:
    """A connection between two entities."""
    subject: str
    predicate: str
    object: str

@dataclass
class Resource:
    """A measurable quantity in the world."""
    name: str
    value: float
    unit: str = ""
    capacity: Optional[float] = None

@dataclass
class WorldState:
    """The complete objective snapshot of reality."""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list)
    resources: Dict[str, Resource] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def get_resource(self, name: str) -> Optional[Resource]:
        return self.resources.get(name)

    def copy(self) -> 'WorldState':
        """Deep-ish copy for persistence and simulation."""
        import copy
        return copy.deepcopy(self)
