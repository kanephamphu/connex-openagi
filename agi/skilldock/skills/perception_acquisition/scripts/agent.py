"""
Perception Acquisition: A meta-skill that allows the AGI to learn new sensing capabilities.
"""

import os
import re
import json
import asyncio
from typing import Dict, Any, List, Optional
from agi.skilldock.base import Skill, SkillMetadata
from agi.brain import GenAIBrain, TaskType
from agi.utils.registry_client import RegistryClient

class PerceptionAcquisitionSkill(Skill):
    """
    Automates the process of creating a new perception module.
    Generates metadata (PERCEPTION.md) and implementation (system.py).
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
        self.registry_client = RegistryClient(config)
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="perception_acquisition",
            description="Acquire a new perception capability by generating metadata and code.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Description of the sensing capability needed (e.g., 'Check CPU temperature')"}
                },
                "required": ["query"]
            },
            output_schema={
                "success": "bool",
                "module_name": "str",
                "message": "str"
            },
            category="meta",
            sub_category="development",
            timeout=300
        )
    
    async def execute(self, query: str) -> Dict[str, Any]:
        """
        Orchestrates the perception generation pipeline.
        """
        # 1. Search Registry First (Remote)
        if self.config.verbose:
            print(f"[PerceptionAcquisition] Searching registry for: {query}")
        
        try:
            remote_results = await self.registry_client.search("perception", query, limit=1)
            if remote_results:
                best = remote_results[0]
                scoped_name = best.get("scopedName") or best.get("name")
                
                if self.config.verbose:
                    print(f"[PerceptionAcquisition] Found remote module '{scoped_name}'. Downloading...")
                
                install_dir = await self.registry_client.download_and_save(
                    "perception", scoped_name, self.config.perception_storage_path
                )
                
                if install_dir:
                    return {
                        "success": True,
                        "module_name": scoped_name,
                        "message": f"Downloaded remote perception module: {scoped_name}"
                    }
        except Exception as e:
            if self.config.verbose:
                print(f"[PerceptionAcquisition] Remote search failed: {e}")

        # 2. Auto-Creation
        module_name = f"auto_sense_{query.lower().replace(' ', '_')[:20]}"
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', module_name)
        
        print(f"[PerceptionAcquisition] 🚀 Starting generation pipeline for '{safe_name}'...")

        try:
            # Step 1: Init PERCEPTION.MD (Metadata)
            print("[PerceptionAcquisition] 1️⃣ Generating Metadata (PERCEPTION.md)...")
            metadata_content = await self._generate_metadata(query, safe_name)
            
            # Step 2: Init system.py (Code)
            print("[PerceptionAcquisition] 2️⃣ Generating Implementation (system.py)...")
            code_content = await self._generate_code(query, safe_name, metadata_content)
            
            # Step 3: Verifying and Saving
            print("[PerceptionAcquisition] 3️⃣ Saving module...")
            
            install_dir = os.path.join(self.config.perception_storage_path, safe_name)
            os.makedirs(install_dir, exist_ok=True)
            
            self._save_file(install_dir, "PERCEPTION.md", metadata_content)
            self._save_file(install_dir, "system.py", code_content)
            
            # Create connex.json for consistency
            connex_json = {
                "name": safe_name,
                "type": "perception",
                "main": "system.py"
            }
            self._save_file(install_dir, "connex.json", json.dumps(connex_json, indent=2))
            
            return {
                "success": True,
                "module_name": safe_name,
                "message": f"Perception '{safe_name}' acquired! Metadata and code generated."
            }

        except Exception as e:
            return {"success": False, "message": f"Perception acquisition failed: {e}"}

    async def _generate_metadata(self, query: str, name: str) -> str:
        example_metadata = """---
name: time_perception
description: "Senses current time and date."
category: system
sub_category: info
version: 0.1.0
---
"""
        prompt = f"""
        Generate the content for PERCEPTION.md for a new Python perception module.
        
        Requirement: {query}
        Name: {name}
        
        REFERENCE EXAMPLE (Follow this structure exactly):
        {example_metadata}
        
        INSTRUCTIONS:
        1. Valid YAML frontmatter is REQUIRED.
        2. 'category' should be one of: system, environment, user, web, hardware.
        3. 'sub_category' should be specific (e.g., info, monitor, visual, auditory).
        
        Generate PERCEPTION.md content:
        """
        return await self._call_llm(prompt)

    async def _generate_code(self, query: str, name: str, metadata: str) -> str:
        example_code = """
import asyncio
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class TimePerception(PerceptionModule):
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="time_perception",
            description="Senses current time and date.",
            category="system",
            sub_category="info",
            version="0.1.0"
        )
    
    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Any:
        import datetime
        now = datetime.datetime.now()
        return {
            "timestamp": now.isoformat(),
            "day": now.strftime("%A"),
            "query_match": True if not query or "time" in query.lower() else False
        }
"""
        prompt = f"""
        Generate the Python implementation (system.py) for the perception module '{name}'.
        
        Requirement: {query}
        Metadata (Contract):
        {metadata}
        
        REFERENCE EXAMPLE (Follow this coding style):
        {example_code}
        
        GUIDELINES:
        1. Inherit from `PerceptionModule` (agi.perception.base).
        2. Implement `connect` (can be creating a client or just setting connected=True).
        3. Implement `perceive(self, query: Optional[str] = None, **kwargs) -> Any`.
        4. Use `metadata` property to identify the module (consistent with PERCEPTION.md).
        5. If external libraries are needed (e.g. psutil, requests), import them inside the method or globally.
        6. Return ONLY valid Python code.
        """
        return await self._call_llm(prompt, extract_code=True)

    async def _call_llm(self, prompt: str, extract_code: bool = False) -> str:
        provider, model = self.brain.select_model(TaskType.CODING)
        client = self.brain.get_client(provider)
        
        text = ""
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
        return text.strip()

    def _extract_code(self, text: str) -> str:
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def _save_file(self, folder, filename, content):
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
            f.write(content)
