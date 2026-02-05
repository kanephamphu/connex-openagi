
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
        """Initialize all registered perception modules with robustness."""
        modules_to_load = [
            (".modules.system_monitor.system", "SystemMonitorPerception", []),
            (".modules.workload.system", "WorkloadPerception", ["identity_manager"]),
            (".modules.voice.system", "VoicePerception", []),
            (".modules.clipboard.system", "ClipboardPerception", []),
            (".modules.time.system", "TimePerception", []),
            (".modules.weather.system", "WeatherPerception", []),
            (".modules.computer_info.system", "ComputerInfoPerception", []),
            (".modules.emotion.system", "EmotionPerception", ["sub_brain_manager"]),
            (".modules.intent_drift.system", "IntentDriftPerception", ["memory_manager"]),
            (".modules.capability.system", "CapabilityPerception", ["skill_registry"])
        ]

        sub_brain = getattr(self.config, 'sub_brain_manager', None)

        for module_path, class_name, deps in modules_to_load:
            try:
                # Dynamic import
                spec = importlib.util.find_spec(module_path, package="agi.perception")
                if not spec:
                    if self.config.verbose:
                        print(f"[Perception] Module path not found: {module_path}")
                    continue
                
                module_lib = importlib.import_module(module_path, package="agi.perception")
                cls = getattr(module_lib, class_name)
                
                # Prepare arguments
                args = {"config": self.config}
                if "memory_manager" in deps and memory_manager:
                    args["memory_manager"] = memory_manager
                if "skill_registry" in deps and skill_registry:
                    args["skill_registry"] = skill_registry
                if "identity_manager" in deps and identity_manager:
                    args["identity_manager"] = identity_manager
                if "sub_brain_manager" in deps:
                    args["sub_brain_manager"] = sub_brain
                
                # Skip if required dependency is missing
                missing_deps = [d for d in deps if d not in args or args[d] is None]
                if missing_deps:
                    if self.config.verbose:
                        print(f"[Perception] Skipping {class_name}: missing deps {missing_deps}")
                    continue

                self.register_module(cls(**args))
                
            except Exception as e:
                if self.config.verbose:
                    print(f"[Perception] Failed to load {class_name}: {e}")
                import traceback
                if self.config.verbose:
                    traceback.print_exc()

        # Generate Embeddings for all successfully loaded modules
        await self.ensure_embeddings()
        
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
            category=getattr(module.metadata, 'category', 'general'),
            sub_category=getattr(module.metadata, 'sub_category', 'general'),
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
                    category = getattr(module.metadata, 'category', 'general')
                    sub_category = getattr(module.metadata, 'sub_category', 'general')
                    text = f"Perception Module {name}: {module.metadata.description}. Category: {category}/{sub_category} (v{module.metadata.version})"
                    vec = await self.brain.get_embedding(text)
                    
                    self.db.register_perception(
                        name=module.metadata.name,
                        description=module.metadata.description,
                        category=category,
                        sub_category=sub_category,
                        type="perception",
                        version=module.metadata.version,
                        embedding=vec
                    )
                    if self.config.verbose:
                        print(f"[Perception] Saved embedding for {name}.")
                except Exception as e:
                    if self.config.verbose:
                        print(f"[Perception] Embedding failed for {name}: {e}")

    async def search_sensors(self, query: str, limit: int = 5) -> List[str]:
        """
        Search for sensors using a combination of vector similarity 
        and keyword boosting (category/description).
        """
        if not query:
            return list(self._modules.keys())[:limit]
            
        # 1. Semantic Vector Search
        results_map = {} # name -> similarity score
        
        if self.config.openai_api_key:
            from agi.brain import GenAIBrain
            if not hasattr(self, 'brain'):
                self.brain = GenAIBrain(self.config)
                
            try:
                query_vec = await self.brain.get_embedding(query)
                matches = self.db.find_similar_perceptions(query_vec, limit=limit*2)
                for m in matches:
                    results_map[m['name']] = 0.5 + (m.get('similarity', 0.5) * 0.5) # Scale similarity
            except Exception as e:
                if self.config.verbose:
                    print(f"[Perception] Vector search failed ({e}).")

        # 2. Keyword Boosting
        query_lower = query.lower()
        active_modules = self._modules.values()
        
        final_scores = []
        for module in active_modules:
            name = module.metadata.name
            score = results_map.get(name, 0.0)
            
            # Boost for category/sub_category match
            category = getattr(module.metadata, 'category', 'general').lower()
            sub_category = getattr(module.metadata, 'sub_category', 'general').lower()
            if category in query_lower or query_lower in category:
                score += 0.5
            if sub_category in query_lower or query_lower in sub_category:
                score += 0.3
                
            # Boost for description keyword match
            desc = module.metadata.description.lower()
            if any(word in desc for word in query_lower.split() if len(word) > 3):
                score += 0.3
                
            if score > 0 or not results_map:
                final_scores.append((name, score))
                
        # 3. Diverse Selection (Highest score per category)
        best_per_group = {}
        for name, score in final_scores:
            module = self._modules.get(name)
            if not module: continue
            
            cat = getattr(module.metadata, 'category', 'general')
            if cat not in best_per_group or score > best_per_group[cat][1]:
                best_per_group[cat] = (name, score)
        
        # Sort best-of-group results by score
        diverse_scored = sorted(best_per_group.values(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in diverse_scored[:limit]]

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
