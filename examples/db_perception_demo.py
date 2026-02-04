
import asyncio
import sqlite3
import os
import json
from agi import AGI
from agi.config import AGIConfig

async def demo_db_perception():
    print("\n" + "="*50)
    print("DEMO: VECTOR PERCEPTION SEARCH")
    print("="*50)
    
    # Ensure fresh DB start for demo
    if os.path.exists("agi_memory.db"):
        os.remove("agi_memory.db")
        print("[Demo] Cleaned up old DB.")
        
    config = AGIConfig.from_env()
    config.verbose = True
    
    agi = AGI(config)
    
    # 1. Initialize (Should sync modules & generate embeddings)
    print("\n[Init] Initializing AGI (Sync + Embedding Gen)...")
    await agi.initialize()
    
    # 2. Verify DB Structure
    print("\n[DB Check] Checking 'embedding' column in 'perceptions'...")
    conn = sqlite3.connect("agi_memory.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(perceptions)")
    columns = [info[1] for info in cursor.fetchall()]
    conn.close()
    
    if "embedding" in columns:
        print("PASS: 'embedding' column exists.")
    else:
        print("FAIL: 'embedding' column missing.")
        return

    # 3. Test Vector/Fallback Search
    # With dummy keys, embedding generation fails, so we test the fallback logic 
    # OR we test that the method is called correctly.
    
    print("\n[Search] Testing search_sensors('weather')...")
    # We expect 'weather' to find 'weather_monitor' via text fallback if embedding failed
    results = await agi.perception.search_sensors("weather")
    print(f"Results for 'weather': {results}")
    
    if "weather" in str(results) or "weather_monitor" in str(results):
         print("PASS: Search returned relevant module.")
    else:
         print("NOTE: Search might be empty if neither vector nor exact match worked.")

    # 4. End-to-End Planner
    print("\n[Planner] Testing Planner Context Discovery...")
    try:
        plan = await agi.planner.create_plan("What is the temperature outside?", context={})
        context = plan.metadata.get("context", {})
        sensor_data = context.get("sensor_data", {})
        print(f"\n[Result] Planner Context: {sensor_data}")
        
    except Exception as e:
        print(f"Planner execution failed (expected with dummy keys): {e}")

if __name__ == "__main__":
    asyncio.run(demo_db_perception())
