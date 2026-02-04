
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from server import app
import server

# Mock AGI and its components
class MockMetadata:
    def __init__(self, name, description="desc", version="1.0"):
        self.name = name
        self.description = description
        self.version = version
        self.signals = []
        self.type = "reflex"

class MockModule:
    def __init__(self, name):
        self.metadata = MockMetadata(name)
        self.active = True

class MockPerceptionLayer:
    def __init__(self):
        self._modules = {
            "test_perception": MockModule("test_perception")
        }
    async def perceive(self, name, query=None):
        return "mock_data"

class MockReflexLayer:
    def __init__(self):
        self._reflexes = {
            "test_reflex": MockModule("test_reflex")
        }

class MockAGI:
    def __init__(self):
        self.perception = MockPerceptionLayer()
        self.reflex = MockReflexLayer()
        self.skill_registry = None # Not needed for this test

@pytest.mark.asyncio
async def test_api_endpoints():
    print("\n" + "="*50)
    print("TEST: API ENDPOINTS")
    print("="*50)
    
    # Inject Mock AGI into server
    server.agi_instance = MockAGI()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Test Perception List
        print("Testing GET /api/perception...")
        resp = await ac.get("/api/perception")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Response: {data}")
        assert "modules" in data
        assert data["modules"][0]["name"] == "test_perception"
        print("PASS")

        # 2. Test Single Perception
        print("\nTesting GET /api/perception/test_perception...")
        resp = await ac.get("/api/perception/test_perception")
        assert resp.status_code == 200
        assert resp.json()["data"] == "mock_data"
        print("PASS")

        # 3. Test Reflex List
        print("\nTesting GET /api/reflex...")
        resp = await ac.get("/api/reflex")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Response: {data}")
        assert "modules" in data
        assert data["modules"][0]["name"] == "test_reflex"
        print("PASS")

if __name__ == "__main__":
    # Rudimentary async run since pytest harness might not be fully set up
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_api_endpoints())
    # Note: This checks basic logic. Real integration depends on AGI init.
