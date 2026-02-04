
import asyncio
from agi.config import AGIConfig
from agi.skilldock.registry import SkillRegistry

async def test_skill_selection():
    print("Testing Semantic Skill Retrieval...")
    
    config = AGIConfig.from_env()
    config.verbose = True # See logs
    
    registry = SkillRegistry(config)
    # Ensure built-ins are loaded
    
    print("\n--- Test 1: Math Query ---")
    query = "Calculate the square root of 144"
    skills = await registry.get_relevant_skills(query, limit=3)
    names = [s.metadata.name for s in skills]
    print(f"Query: {query}")
    print(f"Selected: {names}")
    
    if "code_executor" in names or "calculator" in names:
        print("[PASS] Found execution skill.")
    else:
        print("[FAIL] Math skill not found.")
        
    print("\n--- Test 2: Search Query ---")
    query = "Find information about the latest AI models"
    skills = await registry.get_relevant_skills(query, limit=3)
    names = [s.metadata.name for s in skills]
    print(f"Query: {query}")
    print(f"Selected: {names}")
    
    if "web_search" in names or "http_get" in names:
        print("[PASS] Found search skill.")
    else:
        print("[FAIL] Search skill not found.")
        
    print("\n--- Test 3: Unrelated Query (Confusion Check) ---")
    query = "Write a file to disk"
    skills = await registry.get_relevant_skills(query, limit=3)
    names = [s.metadata.name for s in skills]
    print(f"Selected: {names}")
    
    if "file_manager" in names:
        print("[PASS] Found file_manager.")
        if "web_search" not in names:
            print("[PASS] Successfully excluded unrelated 'web_search'.")
    else:
        print("[FAIL] File manager not found.")

if __name__ == "__main__":
    asyncio.run(test_skill_selection())
