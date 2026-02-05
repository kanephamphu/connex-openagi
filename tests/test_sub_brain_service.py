
import asyncio
import httpx
from unittest.mock import AsyncMock, patch
from agi.config import AGIConfig
from agi.sub_brain import SubBrainServiceManager

async def test_sub_brain_service_init():
    print("Testing Sub-Brain Service Initialization...")
    config = AGIConfig.from_env()
    config.sub_brain_init_command = "mock serve"
    config.sub_brain_health_endpoint = "http://localhost:11434/api/tags"
    
    manager = SubBrainServiceManager(config)
    
    # 1. Test is_healthy success
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(status_code=200)
        healthy = await manager.is_healthy()
        print(f"Health check (healthy): {healthy}")
        assert healthy is True

    # 2. Test is_healthy failure
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        healthy = await manager.is_healthy()
        print(f"Health check (unhealthy): {healthy}")
        assert healthy is False

    # 3. Test service start (mocking subprocess)
    with patch("asyncio.create_subprocess_shell") as mock_subproc:
        mock_subproc.return_value = AsyncMock()
        
        # Patch is_healthy to fail first then succeed
        with patch.object(SubBrainServiceManager, 'is_healthy', side_effect=[False, False, True]):
            started = await manager.start()
            print(f"Service start: {started}")
            assert started is True
            assert mock_subproc.called

    print("SUCCESS: Sub-Brain service initialization verified.")

if __name__ == "__main__":
    asyncio.run(test_sub_brain_service_init())
