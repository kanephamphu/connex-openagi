
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class IdentityProfile:
    name: str = "Connex AGI"
    owner: str = "User"
    version: str = "0.1.0"
    personality: str = "Helpful, Rational, Curious"
    creation_date: str = "2026-02-04"
    
    # Dynamic Health Stats
    ram_usage: float = 0.0
    cpu_usage: float = 0.0
    uptime: float = 0.0
    
    # Custom fields
    traits: Dict[str, Any] = field(default_factory=dict)
    dynamic_states: Dict[str, Any] = field(default_factory=dict)

class IdentityManager:
    """
    Manages the AGI's self-model (Identity, Health, Status).
    """
    
    def __init__(self, config):
        self.config = config
        self.profile = IdentityProfile()
        # Load from config/env if available
        # self.profile.name = config.agent_name ...
        
    def update_health(self, cpu: float, ram: float):
        self.profile.cpu_usage = cpu
        self.profile.ram_usage = ram
        
    def set_state(self, key: str, value: Any):
        """Store a dynamic value in the identity profile."""
        self.profile.dynamic_states[key] = value
        
    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a dynamic value."""
        return self.profile.dynamic_states.get(key, default)
        
    def get_identity_prompt(self) -> str:
        """
        Returns a system prompt segment describing the agent.
        """
        base_prompt = (
            f"You are {self.profile.name}, created by {self.profile.owner}.\n"
            f"Personality: {self.profile.personality}.\n"
            f"Current Health: CPU {self.profile.cpu_usage}%, RAM {self.profile.ram_usage}%.\n"
        )
        if self.profile.dynamic_states:
            base_prompt += f"Current State: {self.profile.dynamic_states}\n"
        return base_prompt

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "name": self.profile.name,
            "owner": self.profile.owner,
            "cpu": self.profile.cpu_usage,
            "ram": self.profile.ram_usage,
            "version": self.profile.version,
            "dynamic_states": self.profile.dynamic_states
        }
