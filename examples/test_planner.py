
import asyncio
import os
from agi.config import AGIConfig
from agi.planner import Planner
from agi.brain import GenAIBrain

async def test_planner_integration():
    print("Testing BrainPlanner Integration...")
    
    # 1. Initialize Config
    config = AGIConfig.from_env()
    print(f"Config loaded. Default Planner: {config.default_planner}")
    
    # 2. Initialize Planner
    planner = Planner(config)
    print(f"Planner initialized: {type(planner).__name__}")
    
    # 3. Verify it has a Brain
    if not hasattr(planner, "brain"):
        print("[FAIL] Planner has no 'brain' attribute")
        return
    
    if not isinstance(planner.brain, GenAIBrain):
        print(f"[FAIL] planner.brain is not GenAIBrain, got {type(planner.brain)}")
        return
        
    print("[PASS] Planner has GenAIBrain attached")
    
    # 4. Verify Model Selection Logic (Mocking if no keys)
    # We can't easily call the API without keys, but we can check the selection logic
    try:
        provider, model = planner.brain.select_model("planning")
        print(f"[PASS] Brain selected: Provider={provider}, Model={model}")
    except ValueError as e:
        print(f"[INFO] Brain selection raised error (likely no keys): {e}")

    print("\nTest Complete.")

if __name__ == "__main__":
    asyncio.run(test_planner_integration())
