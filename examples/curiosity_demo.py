
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_curiosity():
    # 1. Initialize AGI
    print("\n" + "="*50)
    print("DEMO: MOTIVATION 2.0 (Curiosity)")
    print("="*50)
    
    config = AGIConfig.from_env()
    config.verbose = True
    
    # We need to manually init motivation engine as AGI class internal wiring 
    # might effectively hide it or we access it via agi.motivation
    
    agi = AGI(config)
    await agi.initialize()
    
    # Check if motivation engine is exposed
    if not hasattr(agi, 'motivation'):
        print("Motivation engine not directly accessible on AGI instance.")
        # We can instantiate it independently for demo
        from agi.motivation.engine import MotivationEngine
        motivation = MotivationEngine(config, agi.brain)
        print("Instantiated standalone MotivationEngine.")
    else:
        motivation = agi.motivation

    print("\n[State: IDLE]")
    print("Triggering Curiosity Module...")
    
    # 2. Ask for a goal
    proposal = await motivation.propose_curiosity_goal()
    
    if proposal:
        print("\n" + "-"*30)
        print("💡 CURIOSITY TRIGGERED")
        print("-" * 30)
        print(f"Goal: {proposal.get('goal')}")
        print(f"Type: {proposal.get('type')}")
        print(f"Rationale: {proposal.get('rationale')}")
        print(f"Description: {proposal.get('description')}")
        print("-" * 30)
    else:
        print("Curiosity returned no proposal (perhaps error or blocked).")

if __name__ == "__main__":
    asyncio.run(demo_curiosity())
