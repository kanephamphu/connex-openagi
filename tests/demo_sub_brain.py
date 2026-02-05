
import asyncio
import time
from agi.config import AGIConfig
from agi.sub_brain import SubBrainManager

async def run_demo():
    print("=== Sub-Brain Sequential Demo ===")
    config = AGIConfig.from_env()
    
    # Use a single worker for sequential testing
    config.sub_brain_count = 1
    
    manager = SubBrainManager(config)
    
    print(f"[*] Initializing Sub-Brain Manager...")
    await manager.initialize()
    
    # We only test one action now
    task = {"prompt": "Say 'SmolLM is ready and responsive'", "system": "You are a helpful assistant."}
    
    print(f"[*] Running sequential task: {task['prompt']}")
    
    start_time = time.time()
    # We can still use executive_parallel with a single task, or we could add a run_single method.
    # For now, execute_parallel with 1 task is fine for the manager infrastructure.
    results = await manager.execute_parallel([task])
    end_time = time.time()
    
    print("\n=== Result ===")
    print(f"Response: {results[0]}")
    
    print(f"\n[*] Execution time: {end_time - start_time:.2f}s")
    print("===============================")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        print("\nTip: Make sure the SmolLM server is running!")
        print("You can start it with: run_smol_brain.bat")
