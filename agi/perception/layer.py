
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
        self.modules_path = self.config.perception_storage_path
        os.makedirs(self.modules_path, exist_ok=True)
        
        # Initialize Database
        from agi.utils.database import DatabaseManager
        self.db = DatabaseManager()
        
    async def initialize(self, memory_manager=None, skill_registry=None, identity_manager=None):
        """Initialize all registered perception modules."""
        # For demo purposes, load the mock modules
        try:
            from .modules.system_monitor.system import SystemMonitorPerception
            from .modules.workload.system import WorkloadPerception
            from .modules.intent_drift.system import IntentDriftPerception
            from .modules.voice.system import VoicePerception
            from .modules.clipboard.system import ClipboardPerception
            from .modules.time.system import TimePerception
            from .modules.weather.system import WeatherPerception
            
            self.register_module(SystemMonitorPerception(self.config))
            self.register_module(WorkloadPerception(self.config, identity_manager=identity_manager))
            self.register_module(VoicePerception(self.config))
            self.register_module(ClipboardPerception(self.config))
            self.register_module(TimePerception(self.config))
            self.register_module(WeatherPerception(self.config))
            
            if memory_manager:
                self.register_module(IntentDriftPerception(self.config, memory_manager=memory_manager))
                
            if skill_registry:
                from .modules.capability.system import CapabilityPerception
                self.register_module(CapabilityPerception(self.config, skill_registry=skill_registry))
                
            # Async Embedding Generation
            await self.ensure_embeddings()
            
        except ImportError:
            pass
        pass
        
    def register_module(self, module: PerceptionModule):
        """Register a new perception module instance."""
        name = module.metadata.name
        self._modules[name] = module
        
        # Sync to DB
        # Check if we need to generate embedding
        embedding = self.db.get_perception_embedding(name)
        
        if not embedding and self.config.openai_api_key:
            if self.config.verbose:
                print(f"[Perception] Generating embedding for {name}...")
            # We need a Brain instance to generate embeddings
            from agi.brain import GenAIBrain
            if not hasattr(self, 'brain'):
                self.brain = GenAIBrain(self.config)
            
            try:
                # Embed Name + Description + Type
                text = f"{module.metadata.name}: {module.metadata.description} ({module.metadata.version})"
                # Since get_embedding is likely async, we can't call it easily in this sync method if register_module is sync.
                # However, initialize is async, so we can defer embedding or make register_module async?
                # register_module is currently sync.
                # Option: Just schedule it or do it on demand?
                # Best hack for now: Use a helper or assume we can call sync version if available?
                # GenAIBrain usually assumes async.
                # Let's Skip embedding here and do it in a batch `ensure_embeddings` method called from async initialize.
                pass
            except:
                pass

        self.db.register_perception(
            name=module.metadata.name,
            description=module.metadata.description,
            type="perception",
            version=module.metadata.version,
            embedding=embedding # Pass existing (or None)
        )
        
        if self.config.verbose:
            print(f"[Perception] Registered module: {name}")

    async def ensure_embeddings(self):
        """Generate embeddings for all registered modules that lack them."""
        # Check config for key
        if not self.config.openai_api_key:
            return

        from agi.brain import GenAIBrain
        if not hasattr(self, 'brain'):
            self.brain = GenAIBrain(self.config)
            
        for name, module in self._modules.items():
            current_emb = self.db.get_perception_embedding(name)
            if not current_emb:
                try:
                    text = f"{module.metadata.name}: {module.metadata.description} ({module.metadata.version})"
                    vec = await self.brain.get_embedding(text)
                    
                    self.db.register_perception(
                        name=module.metadata.name,
                        description=module.metadata.description,
                        type="perception",
                        version=module.metadata.version,
                        embedding=vec
                    )
                    if self.config.verbose:
                        print(f"[Perception] Saved embedding for {name}.")
                except Exception as e:
                    if self.config.verbose:
                        print(f"[Perception] Embedding failed for {name}: {e}")

    async def search_sensors(self, query: str) -> List[str]:
        """
        Search for sensors using vector similarity.
        Returns list of module names.
        """
        if not self.config.openai_api_key:
            # Fallback to DB generic text search if no key
            results = self.db.search_perceptions(query)
            return [r['name'] for r in results]
            
        from agi.brain import GenAIBrain
        if not hasattr(self, 'brain'):
            self.brain = GenAIBrain(self.config)
            
        try:
            query_vec = await self.brain.get_embedding(query)
            results = self.db.find_similar_perceptions(query_vec)
            return [r['name'] for r in results]
        except Exception as e:
            if self.config.verbose:
                print(f"[Perception] Vector search failed ({e}). Falling back to text search.")
            # Fallback
            results = self.db.search_perceptions(query)
            return [r['name'] for r in results]

    def get_module(self, name: str) -> Optional[PerceptionModule]:
        return self._modules.get(name)
        
    def get_available_sensors(self) -> Dict[str, str]:
        """
        Returns a mapping of sensor names to their descriptions.
        """
        sensors = {}
        for name, module in self._modules.items():
            sensors[name] = module.metadata.description
        return sensors
        
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
