"""
Test script for verifying local skill import functionality.
"""

import os
import shutil
import asyncio
from unittest.mock import MagicMock, patch
from agi import AGI, AGIConfig

# Dummy skill code to simulate a download
DUMMY_SKILL_CODE = """
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata

class CheckLocalImportSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="check_local_import",
            description="Verifies local import works",
            input_schema={"test": "str"},
            output_schema={"status": "str"},
            category="system"
        )
            
    async def execute(self, test: str) -> Dict[str, Any]:
        return {
            "status": f"Imported successfully! Received: {test}",
            "location": __file__
        }
"""

async def main():
    print("=" * 60)
    print("Local Skill Import Verification")
    print("=" * 60)
    
    # Setup test env
    test_storage = "test_installed_skills"
    if os.path.exists(test_storage):
        shutil.rmtree(test_storage)
    os.makedirs(test_storage)
    
    config = AGIConfig()
    config.skills_storage_path = test_storage
    config.verbose = True
    config.deepseek_api_key = "mock_key"
    
    agi = AGI(config)
    
    # Mock the registry response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "@test/check_import",
        "description": "Verifies local import",
        "implementation_code": DUMMY_SKILL_CODE,
        "files": {
            "README.md": "# Test Skill"
        }
    }
    
    print("\n[Action] Mocking registry response and calling install_skill('@test/check_import')...")
    
    # Patch httpx to return our mock
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = asyncio.Future()
        mock_client.get.return_value.set_result(mock_response)
        
        mock_client_cls.return_value = mock_client
        
        success = await agi.skill_registry.install_skill("@test/check_import")
        
    print(f"\n[Result] Install success: {success}")
    
    if success:
        # Verify file existence
        install_path = os.path.join(test_storage, "test_check_import")
        agent_path = os.path.join(install_path, "agent.py")
        exists = os.path.exists(agent_path)
        print(f"[Check] File created at {agent_path}: {exists}")
        
        # Verify execution
        print("\n[Action] Executing installed skill...")
        try:
            skill = agi.skill_registry.get_skill("check_local_import")
            result = await skill.execute(test="System Check")
            print(f"[Result] Execution output: {result}")
            
            if "Imported successfully" in result.get("status", ""):
                print("\n[PASS] Verification PASSED: Skill downloaded, saved, loaded, and executed.")
            else:
                print("\n[FAIL] Verification FAILED: Unexpected output.")
                
        except Exception as e:
            print(f"\n[FAIL] Verification FAILED: {e}")
            import traceback
            traceback.print_exc()
            
    # Cleanup
    # shutil.rmtree(test_storage) 
    print(f"\n(Test artifacts left in {test_storage} for inspection)")

if __name__ == "__main__":
    asyncio.run(main())
