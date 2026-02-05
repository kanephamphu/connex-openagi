
import asyncio
from unittest.mock import AsyncMock, patch
from agi.config import AGIConfig
from agi.sub_brain import SubBrainManager, SubBrainHost

async def test_sub_brain_host_management():
    print("Testing Sub-Brain Host Management...")
    config = AGIConfig.from_env()
    config.sub_brain_init_command = "mock serve"
    config.sub_brain_health_endpoint = "http://localhost:11434/api/tags"
    
    manager = SubBrainManager(config)
    
    # 1. Verify Host Registry
    print(f"Hosts registered: {len(manager.hosts)}")
    assert len(manager.hosts) == 1
    assert isinstance(manager.hosts[0], SubBrainHost)

    # 2. Test Parallel Initialization (Mocking subprocess and health)
    with patch("asyncio.create_subprocess_shell") as mock_subproc:
        mock_subproc.return_value = AsyncMock()
        
        with patch.object(SubBrainHost, 'is_healthy', side_effect=[False, True]):
            initialized = await manager.initialize()
            print(f"Initialization successful: {initialized}")
            assert initialized is True
            assert mock_subproc.called

    # 3. Verify Worker Assignment
    print(f"Workers registered: {len(manager.sub_brains)}")
    assert len(manager.sub_brains) == config.sub_brain_count
    for worker in manager.sub_brains:
        assert worker.host == manager.hosts[0]

    print("SUCCESS: Sub-Brain Host management logic verified.")

if __name__ == "__main__":
    asyncio.run(test_sub_brain_host_management())
