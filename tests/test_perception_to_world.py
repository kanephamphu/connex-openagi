"""
Verification: Perception -> World Pushing Grounding.
"""
print("Starting debug test...")
import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print(f"Python Path: {sys.path}")

import asyncio
from unittest.mock import MagicMock
from agi.config import AGIConfig
from agi.brain import GenAIBrain
from agi.world.manager import WorldManager
from agi.perception.layer import PerceptionLayer

async def test_push_grounding():
    config = AGIConfig.from_env()
    config.verbose = True
    
    brain = MagicMock(spec=GenAIBrain)
    
    # 1. Initialize World
    world = WorldManager(config, brain)
    print(f"Initial Health: {world.state.resources['health'].value}%")
    
    # 2. Initialize Perception & Wire Callback (Push Flow)
    perception = PerceptionLayer(config)
    perception.grounding_callback = world.handle_perception
    
    # 3. Simulate System Monitor Module
    mock_module = MagicMock()
    mock_module.metadata.name = "system_monitor"
    mock_module.connected = True
    
    # Simulate perceived metrics: 90% CPU (High load -> Low health)
    mock_module.perceive = asyncio.coroutine(lambda q=None, **k: {
        "node": "grounding-test-node",
        "metrics": {
            "cpu_percent": 90,
            "disk_free_gb": 200
        }
    })
    
    perception._modules["system_monitor"] = mock_module
    
    # 4. Trigger Perception
    print("\nTriggering Perception (Pushing to World)...")
    await perception.perceive("system_monitor")
    
    # Allow some time for the background task to complete if async
    await asyncio.sleep(0.1)
    
    # 5. Verify World State
    # CPU 90 -> derived_health = 100 - (90/2) = 55
    health = world.state.resources["health"].value
    storage = world.state.resources["storage"].value
    
    print(f"Grounded Health: {health}%")
    print(f"Grounded Storage: {storage} MB")
    
    assert health == 55
    assert storage == 200 * 1024
    
    print("\nSUCCESS: Perception successfully pushed reality-grounding to World Layer!")

if __name__ == "__main__":
    asyncio.run(test_push_grounding())
