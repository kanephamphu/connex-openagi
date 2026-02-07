import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from agi.config import AGIConfig
from agi.motivation.engine import MotivationEngine

async def verify_motivation():
    print("=== Verifying Motivation Engine ===")
    
    # 1. Setup Config
    config = AGIConfig()
    config.verbose = True
    config.motivation_interval = 1
    config.skill_review_min_rating = 4.0
    config.skill_review_min_downloads = 100
    
    # 2. Mock Dependencies
    mock_brain = MagicMock()
    
    # Mock Database
    mock_db = MagicMock()
    mock_db.get_pending_skill_requests.return_value = [
        {"query": "high_quality_skill", "count": 10},
        {"query": "low_quality_skill", "count": 5}, 
        {"query": "missing_skill", "count": 2}
    ]
    
    # Mock Registry Client
    mock_registry_client = AsyncMock()
    
    # Scenario A: High Quality Remote Skill
    # Returns a list of results. One matches criteria.
    skill_hq = {
        "name": "super_skill",
        "scopedName": "connex/super_skill",
        "rating": 4.5,
        "downloads": 200
    }
    
    # Scenario B: Low Quality Remote Skill settings
    skill_lq = {
        "name": "bad_skill",
        "scopedName": "connex/bad_skill", 
        "rating": 3.0,
        "downloads": 10
    }
    
    async def mock_search(type, query):
        if query == "high_quality_skill":
            return [skill_hq]
        if query == "low_quality_skill":
            return [skill_lq]
        return []
        
    mock_registry_client.search.side_effect = mock_search
    
    # Mock Skill Registry (for install)
    mock_skill_registry = AsyncMock()
    mock_skill_registry.install_skill.return_value = True
    
    # Mock Skill Acquisition (for creation)
    mock_acq_skill = AsyncMock()
    mock_acq_skill.execute.return_value = {"success": True}
    
    # 3. Patch and Run
    with patch("agi.utils.database.DatabaseManager", return_value=mock_db), \
         patch("agi.utils.registry_client.RegistryClient", return_value=mock_registry_client), \
         patch("agi.skilldock.registry.SkillRegistry", return_value=mock_skill_registry), \
         patch("agi.skilldock.skills.skill_acquisition.scripts.agent.SkillAcquisitionSkill", return_value=mock_acq_skill):
         
         engine = MotivationEngine(config, mock_brain)
         
         await engine.run_skill_review_cycle()
         
         # 4. Verify Assertions
         
         # Check High Quality -> Install
         print("\n[Check 1] High Quality Skill...")
         # Should have called search
         mock_registry_client.search.assert_any_call("skill", "high_quality_skill")
         # Should have called install
         mock_skill_registry.install_skill.assert_called_with("connex/super_skill")
         # Should have logged success
         mock_db.log_skill_request.assert_any_call("high_quality_skill", status="found_remote")
         print("PASS: Installed high quality skill.")
         
         # Check Low Quality -> Create
         print("\n[Check 2] Low Quality Skill...")
         # Should not install bad skill
         try:
             mock_skill_registry.install_skill.assert_called_with("connex/bad_skill")
             print("FAIL: Should not have installed low quality skill")
         except AssertionError:
             print("PASS: Did not install low quality skill.")
             
         # Should trigger creation
         mock_acq_skill.execute.assert_any_call(requirement="Create a skill for: low_quality_skill")
         mock_db.log_skill_request.assert_any_call("low_quality_skill", status="created")
         print("PASS: Triggered creation for low quality skill.")

         # Check Missing -> Create
         print("\n[Check 3] Missing Skill...")
         mock_acq_skill.execute.assert_any_call(requirement="Create a skill for: missing_skill")
         mock_db.log_skill_request.assert_any_call("missing_skill", status="created")
         print("PASS: Triggered creation for missing skill.")

if __name__ == "__main__":
    asyncio.run(verify_motivation())
