
import asyncio
import time
from agi.config import AGIConfig
from agi.sub_brain import SubBrainManager

async def run_demo():
    print("=== Sub-Brain Intent Classification Demo ===")
    config = AGIConfig.from_env()
    
    # Use multiple workers if available to test parallel execution
    config.sub_brain_count = 2
    
    manager = SubBrainManager(config)
    
    print(f"[*] Initializing Sub-Brain Manager...")
    await manager.initialize()
    
    # Test cases for Intent Classification
    queries = [
        "Hello, how are you today?",
        "What's the weather like in New York?",
        "Open the browser and go to google.com",
        "Tell me a joke",
        "Create a file named hello.txt",
        "Search for Michael Jackson music on YouTube",
        "Who founded Microsoft?"
    ]
    
    tasks = []
    for query in queries:
        prompt = (
            "Task: Classify Input into EXACTLY one category:\n"
            "- CHAT: Greetings, social talk, identity.\n"
            "- WEATHER: Questions about weather/temperature.\n"
            "- WEB_SEARCH: Fact questions, news, searching info.\n"
            "- FILE_OP: Creating, deleting, or managing files/folders.\n"
            "- SYSTEM_CMD: Opening apps, brightness, volume, etc.\n"
            "- PLAN: Complex multi-step requests.\n\n"
            "Example 1: \"Hello\" -> CHAT\n"
            "Example 2: \"How is the weather in Paris?\" -> WEATHER\n"
            "Example 3: \"Who is the president?\" -> WEB_SEARCH\n"
            "Example 4: \"Make a new file called 'test.py'\" -> FILE_OP\n"
            "Example 5: \"Open Chrome\" -> SYSTEM_CMD\n"
            "Example 6: \"Analyze this folder and write a report\" -> PLAN\n"
            f"Input: \"{query}\"\nCategory:"
        )
        tasks.append({
            "prompt": prompt, 
            "system": "You are a precise intent classifier. Respond with exactly one word from the list."
        })
    
    print(f"[*] Dispatching {len(tasks)} classification tasks in parallel...")
    
    start_time = time.time()
    results = await manager.execute_parallel(tasks)
    end_time = time.time()
    
    print("\n=== Intent Classification Results ===")
    for query, intent in zip(queries, results):
        print(f"Query: \"{query[:40]}{'...' if len(query) > 40 else ''}\"")
        print(f"Detected Intent: {intent}")
        print("-" * 30)
    
    print(f"\n[*] Total Execution time: {end_time - start_time:.2f}s")
    print(f"[*] Average time per query: {(end_time - start_time) / len(queries):.2f}s")
    print("===========================================")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        print("\nTip: Make sure the SmolLM server is running!")
        print("You can start it with: run_smol_brain.bat")
