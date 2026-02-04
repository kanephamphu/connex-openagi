"""
Self-correction example - demonstrating plan re-planning on failures.

Shows how the AGI system recovers from failures by creating new plans.
"""

import asyncio
from agi import AGI
from agi.skilldock.base import Skill, SkillMetadata
from typing import Dict, Any


class UnreliableSkill(Skill):
    """
    A skill that sometimes fails - for demonstration purposes.
    """
    
    def __init__(self):
        self.attempts = 0
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="unreliable_fetch",
            description="Fetches data but may fail",
            input_schema={"url": "str"},
            output_schema={"data": "str"},
            category="demo"
        )
    
    async def execute(self, url: str) -> Dict[str, Any]:
        """Execute with 50% failure rate on first attempt."""
        self.attempts += 1
        
        print(f"    [UnreliableSkill] Attempt #{self.attempts} for {url}")
        
        # Fail on first attempt to trigger self-correction
        if self.attempts == 1:
            print(f"    [UnreliableSkill] ❌ Simulating failure...")
            raise Exception("Network timeout - connection lost")
        
        # Succeed on retry
        print(f"    [UnreliableSkill] ✓ Success after self-correction!")
        return {
            "data": f"Data from {url} (retrieved after self-correction)"
        }


async def main():
    """Demonstrate self-correction."""
    
    print("=" * 70)
    print("AGI Self-Correction Example")
    print("=" * 70)
    
    print("\nThis example shows how the AGI system handles failures:")
    print("1. An action fails during execution")
    print("2. The Planner creates a NEW plan for remaining work")
    print("3. Execution continues with the corrected plan")
    print("4. Final goal is still achieved")
    
    # Initialize AGI with self-correction enabled
    agi = AGI()
    
    # Ensure self-correction is enabled
    agi.config.self_correction_enabled = True
    agi.config.verbose = True
    
    # Register unreliable skill
    print("\n📦 Registering unreliable skill...")
    unreliable_skill = UnreliableSkill()
    agi.skill_registry.register(unreliable_skill)
    
    # Goal that will use the unreliable skill
    print("\n🎯 Executing goal...")
    print("=" * 70)
    
    try:
        result = await agi.execute(
            goal="Fetch data from an external API and analyze it",
            context={
                "api_url": "https://api.example.com/data",
                "analysis_type": "sentiment"
            }
        )
        
        print("\n" + "=" * 70)
        print("RESULT")
        print("=" * 70)
        
        if result['success']:
            print("\n✓ Goal achieved despite failure!")
            print(f"\nSteps executed: {result['metadata']['steps_executed']}")
            print(f"Total errors encountered: {len(result['metadata']['errors'])}")
            print(f"\nFinal output: {result['result']}")
            
            print("\n\nExecution Trace:")
            for i, step in enumerate(result['execution_trace'], 1):
                status = "✓" if step['success'] else "✗"
                print(f"{i}. {status} {step['action_id']} ({step.get('duration', 0):.2f}s)")
                if not step['success']:
                    print(f"   Error: {step.get('error', 'Unknown')}")
        else:
            print("\n✗ Goal failed")
            print(f"Errors: {result['metadata']['errors']}")
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


async def demonstrate_without_correction():
    """Show what happens WITHOUT self-correction."""
    
    print("\n\n" + "=" * 70)
    print("Comparison: WITHOUT Self-Correction")
    print("=" * 70)
    
    agi = AGI()
    agi.config.self_correction_enabled = False  # Disable self-correction
    agi.config.verbose = True
    
    unreliable_skill = UnreliableSkill()
    agi.skill_registry.register(unreliable_skill)
    
    print("\n🎯 Running same goal WITHOUT self-correction...")
    print("(This will fail and stop immediately)")
    print("=" * 70)
    
    try:
        result = await agi.execute(
            goal="Fetch data from an external API",
            context={"api_url": "https://api.example.com/data"}
        )
        
        if not result['success']:
            print("\n✗ Failed as expected - no self-correction attempted")
            print(f"Error: {result['errors']}")
    
    except Exception as e:
        print(f"\n✗ Exception raised (fail-fast): {e}")


if __name__ == "__main__":
    # Run both examples
    asyncio.run(main())
    asyncio.run(demonstrate_without_correction())
    
    print("\n\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
With Self-Correction: ✓ Goal achieved despite failures
Without Self-Correction: ✗ Stopped at first error

This demonstrates the AGI-like trait of adapting and recovering from failures,
much like a human would adjust their strategy when encountering obstacles.
    """)
