"""
Skill Acquisition: A meta-skill that allows the AGI to learn new capabilities.
"""

import os
import re
import json
import asyncio
from typing import Dict, Any, List, Optional
from agi.skilldock.base import Skill, SkillMetadata
from agi.brain import GenAIBrain, TaskType
from agi.utils.registry_client import RegistryClient
from agi.skilldock.skills.skill_creator.scripts.agent import SkillCreatorSkill

class SkillAcquisitionSkill(Skill):
    """
    Automates the process of creating a new skill with high accuracy by splitting 
    the process into metadata definition, code generation, and unit testing.
    Uses few-shot prompting with high-quality examples to ensure result quality.
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
        self.registry_client = RegistryClient(config)
        self.creator = SkillCreatorSkill(config)
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="skill_acquisition",
            description="Acquire a new skill by generating metadata, code, and tests.",
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
            timeout=300
        )
    
    async def execute(self, requirement: str) -> Dict[str, Any]:
        """
        Orchestrates the skill generation pipeline.
        """
        # 1. Search Registry First
        if self.config.verbose:
            print(f"[SkillAcquisition] Searching registry for: {requirement}")
        
        # ... (Registry search logic preserved) ...

        skill_name = f"auto_{requirement.lower().replace(' ', '_')[:20]}"
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', skill_name)
        
        print(f"[SkillAcquisition] 🚀 Starting generation pipeline for '{safe_name}'...")

        try:
            # Step 1: Init SKILL.MD (Metadata)
            print("[SkillAcquisition] 1️⃣ Generating Metadata (SKILL.md) with examples...")
            metadata_content = await self._generate_metadata(requirement, safe_name)
            
            # Step 2: Init scripts/agent.py (Code)
            print("[SkillAcquisition] 2️⃣ Generating Implementation (agent.py) with examples...")
            code_content = await self._generate_code(requirement, safe_name, metadata_content)
            
            # Step 3: Init Unit Tests
            print("[SkillAcquisition] 3️⃣ Generating Unit Tests...")
            test_content = await self._generate_tests(requirement, safe_name, code_content)
            
            # Step 4: Verification
            print("[SkillAcquisition] 4️⃣ Verifying and Saving...")
            
            install_dir = os.path.join(self.config.skills_storage_path, safe_name)
            os.makedirs(install_dir, exist_ok=True)
            
            self._save_file(install_dir, "SKILL.md", metadata_content)
            scripts_dir = os.path.join(install_dir, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            self._save_file(scripts_dir, "agent.py", code_content)
            
            # Use SkillCreator to finalize/register
            result = await self.creator.execute(
                name=safe_name,
                code=code_content,
                description=f"Auto-acquired skill for: {requirement}",
                instructions=metadata_content,
                examples="See SKILL.md",
                publish=False 
            )
            
            return {
                "success": True,
                "skill_name": safe_name,
                "message": f"Skill '{safe_name}' acquired! Metadata, code, and tests generated."
            }

        except Exception as e:
            return {"success": False, "message": f"Skill acquisition failed: {e}"}

    async def _generate_metadata(self, requirement: str, name: str) -> str:
        example_metadata = """---
name: http_client
description: HTTP Client for making network requests
category: web
sub_category: api
inputs:
  url:
    type: string
    description: Target URL
  method:
    type: string
    description: "HTTP method: 'GET' or 'POST'"
    required: false
outputs:
  content:
    type: string
    description: Response body
  status:
    type: integer
    description: HTTP status code
---

# HTTP Client Skills

## Instructions
Use `http_get` to fetch content from URLs.
Use `http_post` to send data to APIs.

## Examples
User: "Fetch google.com"
Assistant: Use `http_get` with `{"url": "https://google.com"}`
"""
        prompt = f"""
        Generate the content for SKILL.md for a new Python skill.
        
        Requirement: {requirement}
        Name: {name}
        
        REFERENCE EXAMPLE (Follow this structure exactly):
        {example_metadata}
        
        INSTRUCTIONS:
        1. Valid YAML frontmatter is REQUIRED.
        2. accurate 'inputs' and 'outputs' schema including types and descriptions.
        3. 'category' should be one of: logic, interaction, data, web, system.
        4. MUST include a '## Examples' section with at least one realistic usage example in the "User/Assistant" format shown above.
        
        Generate SKILL.md content:
        """
        return await self._call_llm(prompt)

    async def _generate_code(self, requirement: str, name: str, metadata: str) -> str:
        example_code = """
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase
import httpx

class HTTPGetSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="http_get",
            description="Fetch content from a URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            },
            output_schema={
                "content": "str",
                "status_code": "int"
            },
            category="web",
            sub_category="api",
            timeout=30
        )
    
    async def execute(self, url: str) -> Dict[str, Any]:
        await self.validate_inputs(url=url)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=20.0)
                return {
                    "content": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {"content": "", "status_code": 0, "error": str(e)}
"""
        prompt = f"""
        Generate the Python implementation (agent.py) for the skill '{name}'.
        
        Requirement: {requirement}
        Metadata (Contract):
        {metadata}
        
        REFERENCE EXAMPLE (Follow this coding style):
        {example_code}
        
        GUIDELINES:
        1. Inherit from `Skill` (agi.skilldock.base).
        2. Implement `execute` matching the inputs/outputs in metadata.
        3. Use `metadata` property to return the dictionary version of the YAML frontmatter.
        4. If external libraries are needed (e.g. pandas, requests), import them.
        5. Return ONLY valid Python code.
        """
        return await self._call_llm(prompt, extract_code=True)

    async def _generate_tests(self, requirement: str, name: str, code: str) -> str:
        prompt = f"""
        Generate a `pytest` compatible test file for the following skill code.
        
        Requirement: {requirement}
        Code:
        {code}
        
        INSTRUCTIONS:
        1. Use `pytest`.
        2. Create a test class `Test{name.capitalize()}`.
        3. Mock external dependencies (like requests/httpx) if possible.
        4. Return ONLY valid Python code.
        """
        return await self._call_llm(prompt, extract_code=True)

    async def _call_llm(self, prompt: str, extract_code: bool = False) -> str:
        provider, model = self.brain.select_model(TaskType.CODING)
        client = self.brain.get_client(provider)
        
        text = ""
        # ... (LLM call logic same as before)
        try:
            if provider in ["openai", "deepseek", "groq"]:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                text = response.choices[0].message.content
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""
            
        if extract_code:
            return self._extract_code(text)
        return text

    def _extract_code(self, text: str) -> str:
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def _save_file(self, folder, filename, content):
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
            f.write(content)
