"""
Metaphysical Action: Objective definitions of world interactions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Optional
from agi.world.metaphysical.state import WorldState

@dataclass
class Action:
    """An objective interaction that modifies WorldState."""
    agent: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class EffectRule:
    """A deterministic rule for state transitions."""
    name: str
    check: Callable[[WorldState, Action], bool]
    apply: Callable[[WorldState, Action], WorldState]
    cost: Dict[str, float] = field(default_factory=dict)

class ActionRegistry:
    """Registry for world interaction rules."""
    def __init__(self):
        self.rules: List[EffectRule] = []

    def register(self, rule: EffectRule):
        self.rules.append(rule)

    def find_rule(self, state: WorldState, action: Action) -> Optional[EffectRule]:
        for rule in self.rules:
            if rule.check(state, action):
                return rule
        return None
