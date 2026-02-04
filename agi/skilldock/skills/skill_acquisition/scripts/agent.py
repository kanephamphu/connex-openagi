"""
Skill Acquisition: A meta-skill that allows the AGI to learn new capabilities.
"""

from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase
from agi.brain import GenAIBrain, TaskType

class SkillAcquisitionSkill(Skill):
    """
    Automates the process of creating a new skill to satisfy a missing capability.
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="skill_acquisition",
            description="Acquire a new skill by generating its implementation and registering it.",
            input_schema={
                "type": "object",
                "properties": {
                    "requirement": {"type": "string", "description": "The capability requirement (e.g., 'Extract tables from PDF files')"}
                },
                "required": ["requirement"]
            },
            output_schema={
                "success": "bool",
                "skill_name": "str",
                "message": "str"
            },
            category="meta",
            timeout=180
        )
    
    async def execute(self, requirement: str) -> Dict[str, Any]:
        """
        Generates code for a new skill and calls skill_creator.
        """
        await self.validate_inputs(requirement=requirement)
        
        # 1. Generate skill code using the Brain
        prompt = f"""
        Generate a new Python skill for the Connex AGI ecosystem.
        Requirement: {requirement}
        
        The code MUST be a class inheriting from `Skill` and providing `metadata` and `execute` method.
        
        GUIDELINES:
        1. Use `from typing import Dict, Any, List, Optional`.
        2. Use `from agi.skilldock.base import Skill, SkillMetadata`.
        3. If you need LLM reasoning, use `from agi.brain import GenAIBrain, TaskType` and initialize it in `__init__`.
        4. Do NOT use non-existent modules like `agi.llm`.
        5. Assume you have access to `self.config`.
        
        Example Structure:
        ```python
        from typing import Dict, Any, List, Optional
        from agi.skilldock.base import Skill, SkillMetadata
        from agi.brain import GenAIBrain, TaskType
        
        class MyNewSkill(Skill):
            def __init__(self, config):
                super().__init__(config)
                self.brain = GenAIBrain(config)

            @property
            def metadata(self) -> SkillMetadata:
                # ... define metadata ...
            
            async def execute(self, **kwargs) -> Dict[str, Any]:
                # ... implementation using self.brain ...
        ```
        
        Return ONLY the Python code block.
        """
        
        provider, model = self.brain.select_model(TaskType.CODING)
        client = self.brain.get_client(provider)
        
        try:
            if provider in ["openai", "deepseek", "groq"]:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                code = self._extract_code(response.choices[0].message.content)
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                code = self._extract_code(response.content[0].text)
            else:
                return {"success": False, "message": "Unsupported provider for coding"}
                
            # 2. Call skill_creator (we need to find it in the registry or import it)
            # For simplicity in this implementation, we will use the logic from SkillCreatorSkill
            # or better, assume the Orchestrator can handle the dependency if we return it.
            # But here we are IN a skill. We should probably use the skill_creator logic.
            
            from agi.skilldock.skills.skill_creator.scripts.agent import SkillCreatorSkill
            creator = SkillCreatorSkill(self.config)
            
            skill_name = f"auto_{requirement.lower().replace(' ', '_')[:20]}"
            result = await creator.execute(
                name=skill_name,
                code=code,
                description=f"Auto-acquired skill for: {requirement}",
                instructions=f"Use this skill to {requirement}",
                examples="No examples yet.",
                publish=False # Save locally for now
            )
            
            return {
                "success": result["success"],
                "skill_name": skill_name,
                "message": result["message"]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Skill acquisition failed: {e}"}

    def _extract_code(self, text: str) -> str:
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()
