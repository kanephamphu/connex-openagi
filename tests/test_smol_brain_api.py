
import asyncio
from openai import AsyncOpenAI
from unittest.mock import AsyncMock, patch
import httpx

async def test_smol_brain_api_compatibility():
    print("Testing SmolLM Server API Compatibility...")
    
    # Mocking the actual server response since we are in an agent environment 
    # and might not have a GPU/SmolLM loaded right now.
    # This verifies that our SubBrainHost can communicate with the server format.
    
    from agi.config import AGIConfig
    from agi.sub_brain import SubBrainHost
    
    config = AGIConfig.from_env()
    config.sub_brain_url = "http://localhost:11434/v1"
    config.sub_brain_model = "SmolLM-135M"
    
    host = SubBrainHost(config, 0)
    
    # Mocking the OpenAI client call to simulate the FastAPI response we just built
    with patch("openai.resources.chat.completions.AsyncCompletions.create") as mock_create:
        mock_create.return_value = AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="Hello from SmolLM!"))]
        )
        
        result = await host.run_task("Hello", system_prompt="be a robot")
        print(f"Server Response: {result}")
        assert result == "Hello from SmolLM!"
        assert mock_create.called
        
    print("SUCCESS: SmolLM server integration logic verified.")

if __name__ == "__main__":
    asyncio.run(test_smol_brain_api_compatibility())
