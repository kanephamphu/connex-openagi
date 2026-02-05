
import asyncio
from agi.config import AGIConfig
from agi.sub_brain import SubBrainManager

async def test_sub_brain_parallel():
    print("Testing Sub-Brain Parallel Execution...")
    config = AGIConfig.from_env()
    # Mocking URL for test if not present
    config.sub_brain_url = "http://localhost:11434/v1" 
    
    manager = SubBrainManager(config)
    
    tasks = [
        {"prompt": "Say 'A'", "system": "be precise"},
        {"prompt": "Say 'B'", "system": "be precise"},
        {"prompt": "Say 'C'", "system": "be precise"}
    ]
    
    print(f"Executing {len(tasks)} tasks via {len(manager.sub_brains)} sub-brains...")
    
    # We'll mock the internal client to avoid needing a real Ollama for basic structure test
    from unittest.mock import AsyncMock
    for sb in manager.sub_brains:
        sb.client.chat.completions.create = AsyncMock(return_value=AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="Mocked Response"))]
        ))

    results = await manager.execute_parallel(tasks)
    print(f"Results: {results}")
    
    if len(results) == 3 and all(r == "Mocked Response" for r in results):
        print("SUCCESS: Parallel execution logic verified.")
    else:
        print("FAILURE: Unexpected results.")

if __name__ == "__main__":
    asyncio.run(test_sub_brain_parallel())
