"""
Skill registry for discovering and managing skills.
"""

from typing import Dict, List, Optional, Any
from agi.skilldock.base import Skill, SkillMetadata
from agi.utils.registry_client import RegistryClient


class SkillRegistry:
    """
    Central registry for all available skills.
    
    Discovers, loads, and manages skills.
    """
    
    def __init__(self, config):
        """
        Initialize the skill registry.
        
        Args:
            config: AGIConfig instance
        """
        self.config = config
        self._skills: Dict[str, Skill] = {}
        
        # Initialize SQLite Store
        from agi.skilldock.store import SkillStore
        import os
        db_path = os.path.join(self.config.skills_storage_path, "skills.db")
        self.store = SkillStore(db_path)
        self.registry_client = RegistryClient(self.config)
        
        self._load_builtin_skills()
        self.load_local_skills()
        self._sync_to_store()
    
    def _load_builtin_skills(self):
        """Load built-in skills from the package directory."""
        import os
        
        # Resolve path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        package_dir = os.path.join(current_dir, "skills")
        
        if self.config.verbose:
            print(f"[SkillRegistry] Loading built-in skills from {package_dir}")
            
        # 1. Scan for subdirectories (New Format)
        for entry in os.listdir(package_dir):
            full_path = os.path.join(package_dir, entry)
            if os.path.isdir(full_path):
                self._load_dynamic_skill(full_path)
                
        # 2. Support legacy flat files (during migration)
        # Note: Ideally we remove this once migration is done, but useful for fallback
        # actually, since we are migrating, let's try to load flat files if directories failed?
        # A simple way is to iterate files too.
        # But _load_dynamic_skill expects a directory with agent.py. 
        # For flat files we need standard import.
        
        # Built-in skills are now discovered dynamically by the scanner above.
        # No need for static imports here.
        
        if self.config.verbose:
            print(f"[SkillRegistry] Loaded {len(self._skills)} skills")
    
    def register(self, skill: Skill):
        """
        Register a skill and initialize its isolation environment.
        
        Args:
            skill: Skill instance to register
        """
        name = skill.metadata.name
        if name in self._skills:
            if self.config.verbose:
                print(f"[SkillRegistry] Replacing existing skill: {name}")
        
        # 1. Setup Data Isolation
        import os
        from pathlib import Path
        data_base = Path(self.config.skills_data_path)
        skill_data_dir = data_base / name
        os.makedirs(skill_data_dir, exist_ok=True)
        skill.data_dir = str(skill_data_dir)
        
        # 2. Assign AGI Config
        skill.agi_config = self.config
        
        # 3. Load Persistent Config from Store
        stored_config = self.store.get_skill_config(name)
        if stored_config:
            skill.config.update(stored_config)

        self._skills[name] = skill
        
        if self.config.verbose:
            print(f"[SkillRegistry] Registered skill: {name} (Data: {skill.data_dir})")

    async def initialize_all_skills(self):
        """Initialize all skills: install dependencies and setup environments."""
        if self.config.verbose:
            print(f"[SkillRegistry] Initializing {len(self._skills)} skills...")
            
        for name, skill in self._skills.items():
            await self._setup_skill_environment(skill)
            
    async def _setup_skill_environment(self, skill: Skill):
        """Setup isolated environment for a skill."""
        import os
        import asyncio
        import sys
        import importlib.util
        
        metadata = skill.metadata
        if not metadata.requirements:
            return
            
        # 1. Filter out already installed requirements to save time
        to_install = []
        for req in metadata.requirements:
            # Simple check: take the package name before any version specifier
            pkg_name = req.split('>=')[0].split('==')[0].split('>')[0].split('<')[0].strip()
            # Normalize common names if needed (e.g. playwright vs playwright.async_api is handled by spec)
            if importlib.util.find_spec(pkg_name.replace('-', '_')) is None:
                to_install.append(req)
                
        if not to_install:
            return
            
        if self.config.verbose:
            print(f"[SkillRegistry] Installing requirements for {metadata.name}: {to_install}")
            
        try:
            # Use non-blocking async subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", *to_install,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"[SkillRegistry] Pip install failed for {metadata.name}: {stderr.decode()}")
            else:
                # 2. Post-install hooks (like playwright browser install)
                if any("playwright" in r.lower() for r in to_install):
                    if self.config.verbose:
                        print(f"[SkillRegistry] Installing Playwright browsers for {metadata.name}...")
                    p_proc = await asyncio.create_subprocess_exec(
                        sys.executable, "-m", "playwright", "install", "chromium",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await p_proc.communicate()
                    
        except Exception as e:
            print(f"[SkillRegistry] Unexpected error setup environment for {metadata.name}: {e}")
    
    def unregister(self, skill_name: str):
        """
        Unregister a skill.
        
        Args:
            skill_name: Name of skill to remove
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
    
    def get_skill(self, skill_name: str) -> Skill:
        """
        Get a skill by name.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Skill instance
            
        Raises:
            KeyError: If skill not found
        """
        if skill_name not in self._skills:
            available = ', '.join(self._skills.keys())
            raise KeyError(
                f"Skill '{skill_name}' not found. Available skills: {available}"
            )
        
        return self._skills[skill_name]

    def update_skill_config(self, skill_name: str, new_config: Dict[str, Any]):
        """
        Update skill configuration and persist to DB.
        
        Args:
            skill_name: Name of skill
            new_config: Configuration dictionary to merge
        """
        skill = self.get_skill(skill_name)
        
        # Ensure config is a dict
        if not isinstance(skill.config, dict):
            skill.config = {}
            
        skill.config.update(new_config)
        
        # Save to DB
        self.store.set_skill_config(skill_name, skill.config)
        if self.config.verbose:
            print(f"[SkillRegistry] Updated config for {skill_name}: {new_config}")
    
    def list_skills(self, include_disabled: bool = False) -> List[SkillMetadata]:
        """
        List all registered skills.
        
        Args:
            include_disabled: Whether to include skills that are disabled by user
            
        Returns:
            List of skill metadata
        """
        if include_disabled:
            return [skill.metadata for skill in self._skills.values()]
        
        return [
            skill.metadata for skill in self._skills.values()
            if not isinstance(skill.config, dict) or skill.config.get("enabled", True)
        ]
    def get_skills_by_category(self, category: str) -> List[Skill]:
        """
        Get all skills in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of skills in that category
        """
        return [
            skill for skill in self._skills.values()
            if skill.metadata.category == category
        ]

    async def get_relevant_skills(self, query: str, limit: int = 5, category: str = None, sub_category: str = None) -> List[Skill]:
        """
        Get the most relevant skills for a given query using a combination 
        of semantic search (vector) and keyword boosting (category/description).
        
        Now supports direct boosting for category/sub_category similarity.
        """
        if not query:
             return list(self._skills.values())[:limit]

        # 1. Semantic Vector Search
        relevant_skills = []
        if self.config.openai_api_key:
            # Initialize Brain if not present
            if not hasattr(self, "brain"):
                 from agi.brain import GenAIBrain
                 self.brain = GenAIBrain(self.config)
                 
            try:
                query_vec = await self.brain.get_embedding(query)
                results = self.store.find_relevant_skills(query_vec, limit * 2) # Get more for re-ranking
                
                for meta, score in results:
                    name = meta.get("name")
                    if name in self._skills:
                        skill = self._skills[name]
                        if not isinstance(skill.config, dict) or skill.config.get("enabled", True):
                            relevant_skills.append((skill, score))
            except Exception as e:
                if self.config.verbose:
                    print(f"[Warn] Query embedding failed: {e}")

        # 2. Keyword & Taxonomic Boosting
        # If vector search failed or returned few results, or if we want to boost matches
        query_lower = query.lower()
        
        # Collect all active skills
        active_skills = [s for s in self._skills.values() if not isinstance(s.config, dict) or s.config.get("enabled", True)]
        
        # Build score map from vector results
        score_map = {s.metadata.name: score for s, score in relevant_skills}
        
        final_scored_skills = []
        for skill in active_skills:
            name = skill.metadata.name
            score = score_map.get(name, 0.0)
            
            # Taxonomic Boosting (Priority for similar tools)
            cat = skill.metadata.category.lower()
            sub = getattr(skill.metadata, 'sub_category', 'general').lower()
            
            if category and cat == category.lower():
                score += 0.8 # Strong boost for same category
            if sub_category and sub == sub_category.lower():
                score += 0.4 # Additional boost for same sub-category
                
            # Legacy Keyword Boosting
            if cat in query_lower or query_lower in cat:
                score += 0.3
            if sub in query_lower or query_lower in sub:
                score += 0.1
                
            # Boost for description keyword match
            desc = skill.metadata.description.lower()
            if any(word in desc for word in query_lower.split() if len(word) > 3):
                score += 0.3
                
            if score > 0 or not relevant_skills:
                final_scored_skills.append((skill, score))
        
        # 3. Selection & Diversity
        # For general queries, we want one per category. 
        # For targeted recovery (when category is provided), we want all similar tools.
        if category:
            selected_scored = sorted(final_scored_skills, key=lambda x: x[1], reverse=True)
            selected = [s for s, _ in selected_scored[:limit]]
        else:
            best_per_group = {}
            for skill, score in final_scored_skills:
                cat = skill.metadata.category
                if cat not in best_per_group or score > best_per_group[cat][1]:
                    best_per_group[cat] = (skill, score)
            
            # Extract skills and sort by score
            diverse_scored = sorted(best_per_group.values(), key=lambda x: x[1], reverse=True)
            selected = [s for s, _ in diverse_scored[:limit]]
                
        if self.config.verbose:
            names = [s.metadata.name for s in selected]
            print(f"[SkillRegistry] Selected skills for '{query}': {names}")
            
        return selected

    def _sync_to_store(self):
        """Sync loaded skills metadata to SQLite."""
        for name, skill in self._skills.items():
            # Minimal upsert to ensure existence (embeddings generated async later)
            self.store.upsert_skill(name, skill.metadata.to_dict())

    async def ensure_embeddings(self):
        """Generate and save embeddings for all skills missing them."""
        # Initialize Brain
        if not hasattr(self, "brain"):
             from agi.brain import GenAIBrain
             self.brain = GenAIBrain(self.config)
             
        for name, skill in self._skills.items():
            # Check if embedding exists
            if not self.store.get_embedding(name):
                if self.config.verbose:
                    print(f"[SkillRegistry] Generating embedding for {name}...")
                # Enhanced embedding text
                text = (
                    f"Skill Name: {name}\n"
                    f"Category: {skill.metadata.category}\n"
                    f"Sub-Category: {getattr(skill.metadata, 'sub_category', 'general')}\n"
                    f"Description: {skill.metadata.description}\n"
                    f"Functions/Keywords: {skill.metadata.name.replace('_', ' ')}"
                )
                try:
                    vec = await self.brain.get_embedding(text)
                    # Upsert with embedding
                    self.store.upsert_skill(name, skill.metadata.to_dict(), vec)
                except Exception as e:
                    print(f"[Warn] Failed to embed {name}: {e}")
            else:
                # Ensure metadata is up to date even if embedding exists
                self.store.upsert_skill(name, skill.metadata.to_dict())
    
    async def search_registry(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for skills in the Connex Registry.
        """
        return await self.registry_client.search("skill", query, limit)

    async def install_skill(self, scoped_name: str) -> bool:
        """
        Install a skill from the registry.
        """
        if self.config.verbose:
            print(f"[SkillRegistry] Attempting to install {scoped_name}...")
            
        install_dir = await self.registry_client.download_and_save(
            "skill", scoped_name, self.config.skills_storage_path
        )
        
        if not install_dir:
            return False
            
        return self._load_dynamic_skill(install_dir)

    def _load_dynamic_skill(self, directory: str) -> bool:
        """
        Dynamically load a skill from a directory using importlib.
        
        Args:
            directory: Path to skill directory ensuring it contains agent.py
            
        Returns:
            True if loaded successfully
        """
        import importlib.util
        import sys
        import os
        
        try:
            # 1. Check root agent.py
            agent_path = os.path.join(directory, "agent.py")
            if not os.path.exists(agent_path):
                # 2. Check scripts/agent.py (Anthropic style)
                agent_path = os.path.join(directory, "scripts", "agent.py")
                if not os.path.exists(agent_path):
                    return False
                 
            # Create module name based on directory
            module_name = "installed_skills." + os.path.basename(directory)
            
            spec = importlib.util.spec_from_file_location(module_name, agent_path)
            if not spec or not spec.loader:
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find Skill classes
            loaded_count = 0
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Skill) and attr is not Skill:
                    # Instantiate and register
                    try:
                        # Check if __init__ accepts config
                        import inspect
                        init_sig = inspect.signature(attr.__init__)
                        
                        if "config" in init_sig.parameters:
                            skill_instance = attr(config=self.config)
                        else:
                            skill_instance = attr()
                            
                        # NEW: Inject Schema from SKILL.md if checks pass
                        skill_md_path = os.path.join(directory, "SKILL.md")
                        if os.path.exists(skill_md_path):
                            try:
                                import yaml
                                with open(skill_md_path, "r") as f:
                                    content = f.read()
                                    # Extract YAML frontmatter
                                    if content.startswith("---"):
                                        _, frontmatter, _ = content.split("---", 2)
                                        metadata = yaml.safe_load(frontmatter)
                                        
                                        # Update inputs/outputs in metadata
                                        if "inputs" in metadata:
                                             skill_instance.metadata.input_schema = {
                                                 "type": "object",
                                                 "properties": metadata["inputs"],
                                                 "required": [k for k, v in metadata["inputs"].items() if v.get("required") != False]
                                             }
                                        if "outputs" in metadata:
                                             skill_instance.metadata.output_schema = {
                                                 k: v.get("type", "string") for k,v in metadata["outputs"].items()
                                             }
                            except Exception as e:
                                print(f"[SkillRegistry] Failed to parse SKILL.md for {module_name}: {e}")

                        self.register(skill_instance)
                        loaded_count += 1
                    except Exception as e:
                         print(f"[SkillRegistry] Failed to instantiate {attr_name} in {directory}: {e}")
            
            return loaded_count > 0
            
        except Exception as e:
            print(f"[SkillRegistry] Dynamic load failed for {directory}: {e}")
            return False

    def load_local_skills(self):
        """
        Load all skills from the local storage directory.
        """
        import os
        if not os.path.exists(self.config.skills_storage_path):
            return
            
        if self.config.verbose:
            print(f"[SkillRegistry] Scanning local skills in {self.config.skills_storage_path}...")
            
        for entry in os.listdir(self.config.skills_storage_path):
            full_path = os.path.join(self.config.skills_storage_path, entry)
            if os.path.isdir(full_path):
                self._load_dynamic_skill(full_path)

