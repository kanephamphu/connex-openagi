
from typing import Any, Dict, Optional, List
from agi.perception.base import PerceptionModule, PerceptionMetadata

class CapabilityPerception(PerceptionModule):
    """
    Senses the AGI's own capabilities by querying the SkillRegistry.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="capability_scanner",
            description="Returns information about registered skills and tools.",
            version="1.0.0"
        )
        
    def __init__(self, config, skill_registry):
        super().__init__(config)
        self.skill_registry = skill_registry

    async def connect(self) -> bool:
        # Connection is just having the registry reference
        self.connected = self.skill_registry is not None
        return self.connected

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Returns a summary of available skills.
        
        If 'query' is provided, filters for skills matching the query (naive name/cat filter).
        """
        if not self.connected:
            return {"error": "Skill Registry not connected"}
            
        # Accessing private _skills or using a public method if available.
        # Assuming we can inspect loaded skills.
        # Let's check SkillRegistry interface later, for now assume we can iterate it 
        # or it has a list_skills() method.
        # Based on previous view, it had register and get_skill. We might need to access internals.
        
        skills_info = []
        # Accessing internal dict for now, or assume a get_all_skills method exists
        try:
            # Assuming _skills property or similar
            if hasattr(self.skill_registry, "skills"):
                skill_map = self.skill_registry.skills
            elif hasattr(self.skill_registry, "_skills"):
                skill_map = self.skill_registry._skills
            else:
                return {"error": "Cannot access skill map"}
                
            for name, skill in skill_map.items():
                # Respect enabled flag
                if isinstance(skill.config, dict) and not skill.config.get("enabled", True):
                    continue
                    
                meta = skill.metadata
                skills_info.append({
                    "name": name,
                    "category": meta.category,
                    "description": meta.description
                })
        except Exception as e:
            return {"error": f"Failed to inspect registry: {str(e)}"}

        # Filter if query
        if query:
            query = query.lower()
            skills_info = [s for s in skills_info if query in s["name"].lower() or query in s["category"].lower()]
            
        return {
            "total_count": len(skills_info),
            "skills": skills_info
        }
