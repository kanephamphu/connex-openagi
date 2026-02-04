"""
Demo of Automatic Skill Acquisition.

This shows how the AGI can write code for a new skill and publish it to the registry.
"""

import asyncio
import os
from agi import AGI, AGIConfig

async def main():
    print("=" * 60)
    print("Automatic Skill Acquisition Demo")
    print("=" * 60)
    
    # Setup config
    config = AGIConfig.from_env()
    
    # Enable publishing for this demo
    config.allow_skill_publishing = True
    config.connex_auth_token = os.getenv("CONNEX_AUTH_TOKEN", "mock_token")
    
    # Mock keys if missing to allow AGI init for demo purposes
    if not config.deepseek_api_key:
        config.deepseek_api_key = "mock_key"
    
    agi = AGI(config)
    
    print("\nGoal: 'Create a new skill that calculates Fibonacci numbers and publish it'")
    
    # In a real run, the Planner would decompose this.
    # Here we simulate the execution of the final step: calling 'skill_creator'
    
    skill_creator = agi.skill_registry.get_skill("skill_creator")
    
    # The code the AGI "wrote"
    generated_code = """
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata

class FibonacciSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="fibonacci_calc",
            description="Calculate Nth fibonacci number",
            input_schema={"n": "int"},
            output_schema={"result": "int"},
            category="math"
        )
            
    async def execute(self, n: int) -> Dict[str, Any]:
        if n <= 1: return {"result": n}
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return {"result": b}
"""
    
    print("\n1. Planner decided to create a new skill (@testuser/fibonacci)")
    print("2. Reasoning: 'Math skill missing. I will write and publish it.'")
    print("\n[ACTION] Executing skill_creator...")
    
    # Try to execute (will fail if registry server not running/auth invalid, but shows flow)
    result = await skill_creator.execute(
        name="@testuser/fibonacci",
        code=generated_code,
        description="Calculates Fibonacci sequences efficiently",
        publish=True
    )
    
    print(f"\nResult: {result}")
    
    if result["success"]:
        print(f"\n[SUCCESS] Skill published! ID: {result['skill_id']}")
        print("The AGI can now use '@testuser/fibonacci' in future plans!")
    else:
        # Expected failure in demo env (no real registry running)
        print(f"\n(Note: Failed as expected in demo environment: {result['message']})")
        print("In production, this would register the skill to http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(main())
