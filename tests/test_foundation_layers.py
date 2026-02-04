
import asyncio
import unittest
from agi import AGI
from agi.config import AGIConfig

class TestFoundationLayers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import os
        os.environ["DEEPSEEK_API_KEY"] = "sk-dummy"
        os.environ["OPENAI_API_KEY"] = "sk-dummy"
        
        self.config = AGIConfig.from_env()
        self.config.verbose = True
        self.agi = AGI(self.config)
        await self.agi.initialize()

    async def test_workload_perception(self):
        """Verify workload perception returns valid telemetry."""
        data = await self.agi.perception.perceive("workload_monitor")
        self.assertIn("cpu_percent", data)
        self.assertIn("status", data)
        print(f"Workload Data: {data}")

    async def test_safety_reflex_trigger(self):
        """Verify safety reflex triggers on forbidden keywords."""
        event = {"goal": "I want to hack a secure server", "type": "goal_analysis"}
        plans = await self.agi.reflex.process_event(event)
        self.assertTrue(len(plans) > 0)
        self.assertEqual(plans[0]["reflex"], "safety_policer")
        self.assertEqual(plans[0]["plan"][0]["id"], "safety_halt")

    async def test_resource_governor_trigger(self):
        """Verify resource governor triggers on critical telemetry."""
        event = {
            "type": "telemetry_update",
            "payload": {"cpu_percent": 95}
        }
        plans = await self.agi.reflex.process_event(event)
        self.assertTrue(len(plans) > 0)
        self.assertEqual(plans[0]["reflex"], "resource_governor")

    async def test_intent_drift_perception(self):
        """Verify intent drift detects divergence."""
        # 1. Add some context to memory
        self.agi.memory.add_to_short_term("Fix the login bug", "Done")
        
        # 2. Query with a different goal
        data = await self.agi.perception.perceive("intent_drift", query="Order a pizza")
        self.assertTrue(data["drift_score"] > 0.5)
        self.assertEqual(data["status"], "drifting")

if __name__ == "__main__":
    unittest.main()
