
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
        "Who founded Microsoft?",
        "Explain the process of photosynthesis",
        "Open Calculator"
    ]
    
    tasks = []
    for query in queries:
        prompt = (
            "Task: Classify User Input into EXACTLY one category.\n\n"
            "CATEGORIES:\n"
            "- CHAT: Greetings, social talk, identity, or simple conversational filler.\n"
            "- WEATHER: Questions about weather, temperature, or forecasts.\n"
            "- WEB_SEARCH: Fact questions, current news, searching for specific info online.\n"
            "- RESEARCH: General knowledge, deep information, or requests to 'look up' topics.\n"
            "- FILE_OP: Managing files/folders (create, delete, list, move, read).\n"
            "- SYSTEM_CMD: System-level tasks (open apps, volume, brightness, etc.).\n"
            "- ACTION: Direct singular commands not covered elsewhere.\n"
            "- PLAN: Complex, multi-step requests that require structured reasoning.\n\n"
            "EXAMPLES:\n"
            "\"Hello there\" -> CHAT\n"
            "\"How hot is it in Miami?\" -> WEATHER\n"
            "\"Who won the Oscar yesterday?\" -> WEB_SEARCH\n"
            "\"Explain the concept of quantum entanglement\" -> RESEARCH\n"
            "\"Delete the file 'old.txt'\" -> FILE_OP\n"
            "\"Open Spotify\" -> SYSTEM_CMD\n"
            "\"Research the future of SpaceX and write a report\" -> PLAN\n\n"
            f"Input: \"{query}\"\nCategory:"
        )
        tasks.append({
            "prompt": prompt, 
            "system": "You are a Strategic Intent Classifier. Respond with EXACTLY one word from the list."
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
