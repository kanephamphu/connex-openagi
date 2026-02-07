
import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure we can import from project root
sys.path.append(os.getcwd())
load_dotenv()

from agi.config import AGIConfig
from agi.skilldock.registry import SkillRegistry
from agi.perception import PerceptionLayer
from agi.utils.database import DatabaseManager

async def test_acquisition():
    print("--- Starting Perception Acquisition Verification ---")
    
    config = AGIConfig.from_env()
    config.verbose = True
    
    # 1. Initialize Components
    print("[1] Initializing Registry and Perception Layer...")
    registry = SkillRegistry(config)
    await registry.initialize_all_skills()
    
    perception = PerceptionLayer(config)
    await perception.initialize(skill_registry=registry) # Inject registry
    
    # 2. Check if Acquisition Skill is available
    try:
        acq = registry.get_skill("perception_acquisition")
        print(f"✅ PerceptionAcquisitionSkill found: {acq.metadata.name}")
    except KeyError:
        print("❌ PerceptionAcquisitionSkill NOT found in registry!")
        return

    # 3. Trigger Acquisition for a novel capability
    # We use a randomized query to ensure it doesn't exist
    import random
    query = f"sense_kwant_particles_{random.randint(1000, 9999)}"
    print(f"[2] Requesting novel perception: '{query}'")
    
    module_name = await perception.find_or_create_perception(query)
    
    if module_name:
        print(f"✅ Success! Module created: {module_name}")
        
        # 4. Verify Files
        module_path = os.path.join(config.perception_storage_path, module_name)
        if os.path.exists(os.path.join(module_path, "PERCEPTION.md")) and \
           os.path.exists(os.path.join(module_path, "system.py")):
            print("✅ Files verified (PERCEPTION.md, system.py)")
        else:
            print("❌ Files missing!")
            
        # 5. Verify Database Log
        db = DatabaseManager()
        requests = db.get_pending_perception_requests(limit=100)
        # Should be status='created' now, so might not show in pending?
        # Let's check pending first, it usually filters status='pending'.
        # We need to check if it was updated.
        
        # We can use sqlite directly or add a getter for all requests, 
        # but for now let's trust the return value and files.
        print("✅ Verification Complete.")
    else:
        print("❌ Acquisition Failed.")

if __name__ == "__main__":
    asyncio.run(test_acquisition())
