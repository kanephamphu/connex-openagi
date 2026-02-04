"""
Basic usage example for the AGI system.

Demonstrates how to use all three tiers to accomplish a simple goal.
"""

import asyncio
from agi import AGI


async def main():
    """Run basic AGI example."""
    
    # Initialize AGI system
    # This loads configuration from .env and initializes all three tiers
    agi = AGI()
    
    print("=" * 60)
    print("AGI Basic Usage Example")
    print("=" * 60)
    
    # Example 1: Simple goal
    print("\n--- Example 1: Web Search ---")
    result = await agi.execute(
        goal="Search for information about Python async programming",
        context={"max_results": 3}
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Steps executed: {result['metadata']['steps_executed']}")
    print(f"Duration: {result['metadata']['duration_seconds']}s")
    print(f"\nResult: {result['result']}")
    
    # Example 2: Multi-step goal
    print("\n\n--- Example 2: Multi-step Analysis ---")
    result = await agi.execute(
        goal="Find information about AI agents and create a summary",
        context={
            "format": "bullet points",
            "max_length": 200
        }
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"\nExecution Plan:")
    for i, action in enumerate(result['plan']['actions'], 1):
        print(f"  {i}. {action['description']} ({action['skill']})")
    
    print(f"\nResult: {result['result']}")
    
    # Example 3: Streaming execution
    print("\n\n--- Example 3: Streaming Execution ---")
    
    async for update in agi.execute_with_streaming(
        goal="Research the top 3 upcoming AI trends"
    ):
        phase = update.get("phase")
        update_type = update.get("type")
        
        if phase == "planning" and update_type == "planning_started":
            print(f"\n🧠 Planning started...")
        
        elif phase == "planning" and update_type == "plan_complete":
            plan = update["plan"]
            print(f"✓ Plan created with {len(plan.actions)} actions")
        
        elif phase == "execution" and update_type == "action_started":
            print(f"\n⚡ Executing: {update['description']}")
        
        elif phase == "execution" and update_type == "action_completed":
            print(f"  ✓ Completed in {update['duration']:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
