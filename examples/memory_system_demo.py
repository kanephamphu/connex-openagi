
import asyncio
import json
from agi import AGI
from agi.config import AGIConfig

async def demo_memory_system():
    # 1. Initialize AGI
    config = AGIConfig.from_env()
    config.verbose = True
    agi = AGI(config)
    await agi.initialize()
    
    print("\n" + "="*50)
    print("DEMO: MEMORY SYSTEM (Short-Term & Long-Term)")
    print("="*50)
    
    # 2. Simulate an interaction (Chat)
    goal = "Who is the CEO of Connex?"
    print(f"\n[ST Memory] Simulating interaction: {goal}")
    
    # We call execute which will trigger add_to_short_term at the end
    async for update in agi.execute_with_streaming(goal):
        if update.get("type") == "action_completed" and update.get("action_id") == "chat_response":
             print(f"AGI Response: {update['output']['reply'][:50]}...")
             
    # 3. Verify Short-Term context
    context_window = agi.memory.get_context_window()
    print(f"\n[ST Memory] Current Context Window:\n{context_window}")
    
    # 4. Simulate Daily Summarization (Moving ST to LT)
    print("\n" + "="*50)
    print("DEMO: DAILY SUMMARIZATION (History -> Summary -> SQLite)")
    print("="*50)
    
    # Since we just ran one task, we have history. 
    # Let's trigger the summarization.
    await agi.memory.summarize_and_persist(agi.history)
    
    # 5. Semantic Recall (Querying SQLite)
    print("\n" + "="*50)
    print("DEMO: SEMANTIC RECALL (Skill: memory_recall)")
    print("="*50)
    
    # Ask the AGI to remember something based on recent "Experience"
    # In a real plan, the Planner would use the 'memory_recall' skill.
    # Here we invoke the skill directly.
    memory_skill = agi.skill_registry.get_skill("memory_recall")
    
    result = await memory_skill.execute(query="Connex CEO info", limit=2)
    print(f"Recall Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(demo_memory_system())
