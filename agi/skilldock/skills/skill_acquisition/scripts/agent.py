"""
Skill Acquisition: A meta-skill that allows the AGI to learn new capabilities.
"""

from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase
from agi.brain import GenAIBrain, TaskType
from agi.utils.registry_client import RegistryClient

class SkillAcquisitionSkill(Skill):
    """
    Automates the process of creating a new skill to satisfy a missing capability.
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
        self.registry_client = RegistryClient(config)
    
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
            sub_category="development",
            timeout=180
        )
    
    async def execute(self, requirement: str) -> Dict[str, Any]:
        """
        Generates code for a new skill and calls skill_creator.
        await self.validate_inputs(requirement=requirement)
        
        # 1. First, search the Connex Registry for an existing skill
        if self.config.verbose:
            print(f"[SkillAcquisition] Searching registry for: {requirement}")
            
        search_results = await self.registry_client.search("skill", requirement, limit=3)
        
        if search_results:
            # Simple heuristic: if we find something that looks like 
            # it matches, we try to install it.
            # In a more advanced version, we could use the LLM to verify 
            # if the registry result matches the requirement.
            best_match = search_results[0]
            scoped_name = best_match.get("scopedName") or best_match.get("name")
            
            if scoped_name:
                if self.config.verbose:
                    print(f"[SkillAcquisition] Found potential match in registry: {scoped_name}. Attempting install...")
                
                # We need access to the SkillRegistry to install it. 
                # Since skills don't have it, we use the server's pattern: RegistryClient + dynamic load.
                install_dir = await self.registry_client.download_and_save(
                    "skill", scoped_name, self.config.skills_storage_path
                )
                
                if install_dir:
                    # We can't easily trigger the main SkillRegistry to load it from here 
                    # without more wiring, but the Orchestrator will see it next time 
                    # it asks the registry for skills if we reload.
                    # For now, let's just return success if it's saved.
                    return {
                        "success": True,
                        "skill_name": scoped_name,
                        "message": f"Successfully found and installed '{scoped_name}' from the Connex Registry."
                    }

        # 2. Fallback: Generate skill code using the Brain
        if self.config.verbose:
            print(f"[SkillAcquisition] No suitable skill found in registry. Generating new implementation...")
        
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
