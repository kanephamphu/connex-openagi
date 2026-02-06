import os
import importlib.util
import sys
from typing import Dict, List, Optional, Any
from agi.config import AGIConfig
from agi.reflex.base import ReflexModule
from agi.planner.base import ActionPlan, ActionNode
from agi.utils.registry_client import RegistryClient

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
        self.registry_client = RegistryClient(self.config)
        
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
             
        # Load Local Reflexes from storage path
        self.load_local_reflexes()
        
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

    async def install_reflex(self, scoped_name: str) -> bool:
        """
        Install a reflex module from the registry.
        """
        if self.config.verbose:
            print(f"[Reflex] Attempting to install {scoped_name}...")
            
        install_dir = await self.registry_client.download_and_save(
            "reflex", scoped_name, self.modules_path
        )
        
        if not install_dir:
            return False
            
        return self._load_dynamic_reflex(install_dir)

    def _load_dynamic_reflex(self, directory: str) -> bool:
        """
        Dynamically load a reflex module from a directory.
        """
        import importlib.util
        import sys
        import os
        
        try:
            # Main file from connex.json or default to system.py
            main_file = "system.py"
            manifest_path = os.path.join(directory, "connex.json")
            if os.path.exists(manifest_path):
                import json
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                    main_file = manifest.get("main", "system.py")
            
            agent_path = os.path.join(directory, main_file)
            if not os.path.exists(agent_path):
                return False
                 
            module_name = "installed_reflex." + os.path.basename(directory)
            
            spec = importlib.util.spec_from_file_location(module_name, agent_path)
            if not spec or not spec.loader:
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            loaded_count = 0
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ReflexModule) and attr is not ReflexModule:
                    try:
                        # Instantiate
                        instance = attr(config=self.config)
                        self.register_reflex(instance)
                        loaded_count += 1
                    except Exception as e:
                         print(f"[Reflex] Failed to instantiate {attr_name}: {e}")
            
            return loaded_count > 0
            
        except Exception as e:
            print(f"[Reflex] Dynamic load failed for {directory}: {e}")
            return False

    def load_local_reflexes(self):
        """Load all reflex modules from storage."""
        if not os.path.exists(self.modules_path):
            return
            
        for entry in os.listdir(self.modules_path):
            full_path = os.path.join(self.modules_path, entry)
            if os.path.isdir(full_path):
                self._load_dynamic_reflex(full_path)

    async def search_registry(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the registry for reflex modules."""
        return await self.registry_client.search("reflex", query, limit)
