
import asyncio
import os
from agi.config import AGIConfig
from agi.skilldock.skills.memory.scripts.agent import MemorySkill

async def test_semantic_memory():
    print("Testing Semantic Memory (The Soul)...")
    
    config = AGIConfig.from_env()
    
    # Check if we have an embedding key (OpenAI usually)
    if not config.openai_api_key:
        print("[SKIP] No OPENAI_API_KEY found, cannot test embeddings/semantic memory functionality.")
        return

    # Initialize
    mem = MemorySkill(config)
    mem.engine.db_path = "test_soul.db" # Use test DB
    mem.engine._init_db()
    
    print("\n1. Storing Facts...")
    facts = [
        "The user's name is Ptai.",
        "The user loves coding in Python.",
        "The user hates waiting for slow computations.",
        "The project is about building an AGI system."
    ]
    
    for fact in facts:
        await mem.execute("store", content=fact)
        print(f"Stored: {fact}")
        
    print("\n2. Testing Semantics (Recall)...")
    
    # Test 1: name (Semantic match: "Who am I?" -> "name is Ptai")
    q1 = "Who am I?"
    res1 = await mem.execute("recall", content=q1)
    print(f"Query: '{q1}'")
    
    found = False
    if res1.get("success"):
        for m in res1.get("results", []):
            print(f" - Found ({m['score']:.2f}): {m['content']}")
            if "Ptai" in m['content']:
                found = True
    
    if found: print("[PASS] Recalled Name")
    else: print("[FAIL] Did not recall name")

    # Test 2: preferences (Semantic match: "dislikes" -> "hates waiting")
    q2 = "What does the user dislike?"
    res2 = await mem.execute("recall", content=q2)
    print(f"Query: '{q2}'")
    
    found = False
    if res2.get("success"):
        for m in res2.get("results", []):
            print(f" - Found ({m['score']:.2f}): {m['content']}")
            if "waiting" in m['content']:
                found = True

    if found: print("[PASS] Recalled Dislike")
    else: print("[FAIL] Did not recall dislike")
    
    # Cleanup
    try:
        if os.path.exists("test_soul.db"):
            os.remove("test_soul.db")
    except: pass

    print("\nSoul Memory Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_semantic_memory())
