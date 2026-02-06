"""
Backward compatibility wrapper for SkillPublisher.
"""
from typing import Dict, Any, Optional
from agi.services.publisher import ConnexPublisher
from agi.config import AGIConfig

class SkillPublisher:
    """ Wrapper for ConnexPublisher for backward compatibility. """
    def __init__(self, config: AGIConfig):
        self.config = config
        self.inner = ConnexPublisher(config)
        
    async def publish_skill(
        self, 
        name: str, 
        code: str, 
        description: str,
        files: Optional[Dict[str, str]] = None,
        category: str = "utilities"
    ) -> Dict[str, Any]:
        # Create a dummy skill instance to use the generic publisher
        from agi.skilldock.base import Skill, SkillMetadata
        
        class DummySkill(Skill):
             @property
             def metadata(self):
                 return SkillMetadata(
                     name=name,
                     description=description,
                     category=category,
                     input_schema={},
                     output_schema={}
                 )
             async def execute(self, **kwargs): pass

        dummy = DummySkill(self.config)
        # Hack to inject the code if it's coming from an external string rather than class source
        # But the generic publisher tries to read the file. 
        # For SkillCreator, it passes the code explicitly.
        
        # Let's just use the inner publisher directly with a small adjustment if needed 
        # or just reimplement the direct publish here to avoid over-complicating.
        
        return await self.inner.publish_component(
            component=dummy,
            scoped_name=name,
            code=code,
            files=files
        )
