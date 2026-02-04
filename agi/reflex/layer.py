
import os
from typing import Dict, List, Optional, Any
from agi.config import AGIConfig
from agi.reflex.base import ReflexModule

class ReflexLayer:
    """
    Manages the AGI's Unconditional Reflexes.
    Listens for events (webhooks, signals) and triggers registered Reflex Modules.
    """
    
    def __init__(self, config: AGIConfig):
        self.config = config
        self._reflexes: Dict[str, ReflexModule] = {}
        self.modules_path = os.path.join(self.config.data_dir, "reflex_modules")
        os.makedirs(self.modules_path, exist_ok=True)
        
    def register_reflex(self, reflex: ReflexModule):
        """Register a new reflex module."""
        name = reflex.metadata.name
        self._reflexes[name] = reflex
        if self.config.verbose:
            print(f"[Reflex] Registered reflex: {name}")

    async def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process an incoming event against all active reflexes.
        Returns a list of Plans (actions) from triggered reflexes.
        """
        triggered_plans = []
        
        for name, reflex in self._reflexes.items():
            if not reflex.active:
                continue
                
            try:
                should_trigger = await reflex.evaluate(event)
                if should_trigger:
                    if self.config.verbose:
                        print(f"[Reflex] Triggered: {name}")
                    plan = await reflex.get_plan()
                    triggered_plans.append({
                        "reflex": name,
                        "plan": plan
                    })
            except Exception as e:
                print(f"[Reflex] Error evaluating {name}: {e}")
                
        return triggered_plans

    async def install_reflex(self, source_path_or_url: str):
        """
        Install a reflex module.
        """
        pass
