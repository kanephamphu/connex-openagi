
import os
from typing import Dict, List, Optional, Any
from agi.config import AGIConfig
from agi.reflex.base import ReflexModule
from agi.planner.base import ActionPlan, ActionNode

class ReflexLayer:
    """
    Manages the AGI's Unconditional Reflexes.
    Listens for events (webhooks, signals) and triggers registered Reflex Modules.
    """
    
    def __init__(self, config: AGIConfig):
        self.config = config
        self._reflexes: Dict[str, ReflexModule] = {}
        self.modules_path = self.config.reflex_storage_path
        os.makedirs(self.modules_path, exist_ok=True)
        
    async def initialize(self, history_manager=None):
        # Demo loading
        try:
             from .modules.auto_recovery.system import AutoRecoveryReflex
             from .modules.safety.system import SafetyPolicyReflex
             from .modules.governor.system import ResourceGovernorReflex
             from .modules.voice_command.system import VoiceCommandReflex
             from .modules.smart_clipboard.system import ClipboardReflex
             from .modules.scheduler.system import SchedulerReflex
             from .modules.weather_alert.system import WeatherAlertReflex
             from .modules.time_handlers.calendar_handler import CalendarReflex
             from .modules.time_handlers.deadline_handler import DeadlineReflex
             from .modules.time_handlers.healthcare_handler import HealthcareReflex
             
             self.register_reflex(AutoRecoveryReflex(self.config))
             self.register_reflex(SafetyPolicyReflex(self.config))
             self.register_reflex(ResourceGovernorReflex(self.config))
             self.register_reflex(VoiceCommandReflex(self.config))
             self.register_reflex(ClipboardReflex(self.config))
             self.register_reflex(SchedulerReflex(self.config))
             self.register_reflex(WeatherAlertReflex(self.config))
             self.register_reflex(CalendarReflex(self.config))
             self.register_reflex(DeadlineReflex(self.config))
             self.register_reflex(HealthcareReflex(self.config))
             
             if history_manager:
                 from .modules.self_repair.system import SelfRepairReflex
                 self.register_reflex(SelfRepairReflex(self.config, history_manager=history_manager))
        except ImportError:
             pass
        
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
                    plan_data = await reflex.get_plan()
                    
                    # Convert list of dicts to ActionPlan
                    actions = [ActionNode(**a) for a in plan_data]
                    plan = ActionPlan(
                        goal=f"Reflex Trigger: {name}",
                        actions=actions,
                        reasoning=f"Triggered by reflex module {name}"
                    )
                    
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
