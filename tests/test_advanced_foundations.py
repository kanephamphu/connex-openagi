
import unittest
from unittest.mock import MagicMock
from agi.perception.modules.capability.system import CapabilityPerception
from agi.reflex.modules.self_repair.system import SelfRepairReflex
from agi.config import AGIConfig

class TestAdvancedFoundations(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = AGIConfig.from_env()

    async def test_capability_perception(self):
        # Mock Skill Registry
        mock_registry = MagicMock()
        mock_skill = MagicMock()
        mock_skill.metadata.category = "test"
        mock_skill.metadata.description = "A test skill"
        mock_registry.skills = {"test_skill": mock_skill}
        
        module = CapabilityPerception(self.config, mock_registry)
        await module.connect()
        
        # Test full list
        result = await module.perceive()
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["skills"][0]["name"], "test_skill")
        
        # Test query
        result = await module.perceive(query="test")
        self.assertEqual(len(result["skills"]), 1)
        
        # Test no match
        result = await module.perceive(query="nomatch")
        self.assertEqual(len(result["skills"]), 0)

    async def test_self_repair_reflex(self):
        # Mock History Manager
        mock_history = MagicMock()
        # Simulate 3 failures
        mock_history.get_recent.return_value = [
            {"status": "failed", "error": "broken"},
            {"status": "failed", "error": "broken"},
            {"status": "failed", "error": "broken"}
        ]
        
        reflex = SelfRepairReflex(self.config, mock_history)
        
        # Test trigger event
        event = {"type": "health_check"}
        should_trigger = await reflex.evaluate(event)
        self.assertTrue(should_trigger)
        
        # Verify plan
        plans = await reflex.get_plan()
        self.assertEqual(plans[0]["id"], "run_diagnostics")

if __name__ == "__main__":
    unittest.main()
