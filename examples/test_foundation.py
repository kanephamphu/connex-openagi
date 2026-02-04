
import asyncio
import os
from agi.config import AGIConfig
from agi.skilldock.skills.file_manager.scripts.agent import FileManagerSkill
from agi.skilldock.skills.memory.scripts.agent import MemorySkill

async def test_foundation_skills():
    print("Testing Foundation Skills...")
    config = AGIConfig.from_env()

    # --- Test File Manager ---
    print("\n[File Manager]")
    fm = FileManagerSkill(config)
    
    # Write
    await fm.execute("write_file", "test_foundation.txt", "Foundation Skill Test")
    print("Write: Done")
    
    # Read
    res = await fm.execute("read_file", "test_foundation.txt")
    if res.get("success") and res.get("data") == "Foundation Skill Test":
        print("[PASS] File Write/Read")
    else:
        print(f"[FAIL] File Read: {res}")
        
    # List
    res = await fm.execute("list_directory", ".")
    if "test_foundation.txt" in res.get("data", []):
         print("[PASS] List Directory")
    else:
         print(f"[FAIL] List Directory: {res}")
         
    # Cleanup
    try:
        os.remove("test_foundation.txt")
    except: pass

    # --- Test Memory ---
    print("\n[Memory]")
    mem = MemorySkill(config)
    mem.memory_file = "test_memory.json" # Use test file
    
    # Store
    await mem.execute("store", "test_key", "test_value")
    print("Store: Done")
    
    # Retrieve
    res = await mem.execute("retrieve", "test_key")
    if res.get("success") and res.get("value") == "test_value":
        print("[PASS] Memory Store/Retrieve")
    else:
        print(f"[FAIL] Memory Retrieve: {res}")
        
    # Forget
    await mem.execute("forget", "test_key")
    res = await mem.execute("retrieve", "test_key")
    if not res.get("success"):
        print("[PASS] Memory Forget")
    else:
         print(f"[FAIL] Memory Forget Failed: {res}")
         
    # Cleanup
    if os.path.exists("test_memory.json"):
        os.remove("test_memory.json")

    print("\nFoundation Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_foundation_skills())
