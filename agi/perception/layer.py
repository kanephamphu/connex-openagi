
import os
import importlib.util
from typing import Dict, List, Optional, Any
from agi.config import AGIConfig
from agi.perception.base import PerceptionModule

class PerceptionLayer:
    """
    Manages the AGI's perception capabilities.
    Acts as the 'harness' for loading and querying specific Perception Modules.
    """
    
    def __init__(self, config: AGIConfig):
        self.config = config
        self._modules: Dict[str, PerceptionModule] = {}
        # Path to where dynamic modules are stored/installed
        self.modules_path = os.path.join(self.config.data_dir, "perception_modules")
        os.makedirs(self.modules_path, exist_ok=True)
        
    async def initialize(self):
        """Initialize all registered perception modules."""
        # Load built-ins or saved modules here
        pass
        
    def register_module(self, module: PerceptionModule):
        """Register a new perception module instance."""
        name = module.metadata.name
        self._modules[name] = module
        if self.config.verbose:
            print(f"[Perception] Registered module: {name}")

    def get_module(self, name: str) -> Optional[PerceptionModule]:
        return self._modules.get(name)
        
    async def perceive(self, module_name: str, query: Optional[str] = None, **kwargs) -> Any:
        """
        Request perception from a specific module.
        """
        module = self._modules.get(module_name)
        if not module:
            raise ValueError(f"Perception module '{module_name}' not found.")
            
        if not module.connected:
            await module.connect()
            
        return await module.perceive(query, **kwargs)

    async def install_module(self, source_path_or_url: str):
        """
        Install a perception module from a registry or path.
        (Placeholder for dynamic loading logic similar to SkillRegistry)
        """
        pass
