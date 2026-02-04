"""
Skill that allows the AGI to create and publish new skills.
"""

from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase
from agi.skilldock.publisher import SkillPublisher


class SkillCreatorSkill(Skill):
    """
    Auotonomously creates and publishes new skills to the Connex ecosystem.
    """
    
    def __init__(self, config):
        self.config = config
        self.publisher = SkillPublisher(config)
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="skill_creator",
            description="Create and publish a new Python skill to the registry",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name (e.g., @user/skill)"},
                    "code": {"type": "string", "description": "Python implementation code"},
                    "description": {"type": "string", "description": "Skill description"},
                    "instructions": {"type": "string", "description": "Detailed usage instructions (Markdown)"},
                    "examples": {"type": "string", "description": "Usage examples (Markdown)"},
                    "publish": {"type": "boolean", "description": "Whether to publish to registry", "default": True}
                },
                "required": ["name", "code", "description", "instructions", "examples"]
            },
            output_schema={
                "success": "bool",
                "skill_id": "str",
                "message": "str"
            },
            category="development",
            timeout=120,
            tests=[
                SkillTestCase(
                    description="Validate code without publishing",
                    input={
                        "name": "@test/dummy",
                        "code": "print('hello')",
                        "description": "A dummy skill",
                        "instructions": "Run it.",
                        "examples": "Just run.",
                        "publish": False
                    },
                    assertions=[
                        "Success is True",
                        "Message confirms code validation",
                        "Skill ID is 'local-only'"
                    ]
                )
            ]
        )
    
    async def execute(
        self, 
        name: str, 
        code: str, 
        description: str,
        instructions: str,
        examples: str,
        publish: bool = True
    ) -> Dict[str, Any]:
        """
        Execute skill creation.
        """
        await self.validate_inputs(
            name=name, code=code, description=description, 
            instructions=instructions, examples=examples, publish=publish
        )
        
        # 0. Generate SKILL.md content
        clean_name = name.split("/")[-1] if "/" in name else name
        skill_md = f"""---
name: {clean_name}
description: {description}
---

# {clean_name}

## Instructions
{instructions}

## Examples
{examples}
"""
        
        # 1. Validate code (basic syntax check)
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            return {
                "success": False,
                "skill_id": "",
                "message": f"Code syntax error: {str(e)}"
            }
            
        if not publish:
            # Install locally if not publishing
            import os
            import json
            
            try:
                # Sanitization
                safe_name = name.replace("@", "").replace("/", "_")
                install_dir = os.path.join(self.config.skills_storage_path, safe_name)
                os.makedirs(install_dir, exist_ok=True)
                
                # Write agent.py
                agent_dir = os.path.join(install_dir, "scripts")
                os.makedirs(agent_dir, exist_ok=True)
                
                with open(os.path.join(agent_dir, "agent.py"), "w", encoding="utf-8") as f:
                    f.write(code)
                    
                # Write SKILL.md
                with open(os.path.join(install_dir, "SKILL.md"), "w", encoding="utf-8") as f:
                    f.write(skill_md)
                    
                # Write manifest (connex.json) minimal version for local loading
                manifest = {
                    "name": name,
                    "description": description,
                    "version": "0.1.0-local",
                    "category": "development",
                    "files": {"SKILL.md": skill_md}
                }
                with open(os.path.join(install_dir, "connex.json"), "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                    
                return {
                    "success": True,
                    "skill_id": name,
                    "message": f"Skill saved locally to {install_dir} (code in scripts/)"
                }
            except Exception as e:
                return {
                    "success": False,
                    "skill_id": "",
                    "message": f"Local save failed: {str(e)}"
                }
        
        # 2. Publish to registry
        try:
            if not self.config.connex_auth_token:
                return {
                    "success": False,
                    "skill_id": "",
                    "message": "CONNEX_AUTH_TOKEN not configured. Cannot publish."
                }
                
            # Include SKILL.md in the file bundle
            files = {
                "SKILL.md": skill_md
            }
                
            result = await self.publisher.publish_skill(
                name=name,
                code=code,
                description=description,
                files=files
            )
            
            return {
                "success": True,
                "skill_id": result.get("id", name),
                "message": f"Successfully published {name} to registry"
            }
            
        except Exception as e:
            return {
                "success": False,
                "skill_id": "",
                "message": f"Publishing failed: {str(e)}"
            }
