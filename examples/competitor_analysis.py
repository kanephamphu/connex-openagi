"""
Competitor analysis example - the use case from your description.

Demonstrates how the AGI system breaks down a complex business goal
into executable steps.
"""

import asyncio
from agi import AGI


async def main():
    """Run competitor analysis example."""
    
    print("=" * 70)
    print("AGI Competitor Analysis Example")
    print("=" * 70)
    
    # Initialize AGI
    agi = AGI()
    
    # Complex goal: Analyze competitors
    goal = "Analyze my brand's competitors in the SaaS marketing automation space"
    
    context = {
        "brand": "Govairo",
        "industry": "SaaS",
        "category": "Marketing Automation",
        "region": "Global",
        "focus_areas": [
            "pricing",
            "features",
            "market share",
            "customer reviews"
        ]
    }
    
    print(f"\n🎯 Goal: {goal}")
    print(f"\n📋 Context:")
    for key, value in context.items():
        print(f"  • {key}: {value}")
    
    # Execute with streaming to show the thinking process
    print("\n" + "=" * 70)
    print("EXECUTION")
    print("=" * 70)
    
    async for update in agi.execute_with_streaming(goal, context):
        phase = update.get("phase")
        update_type = update.get("type")
        
        # Planning phase
        if phase == "planning":
            if update_type == "planning_started":
                print("\n🧠 TIER 1: PLANNER (Architect) - Decomposing goal...")
            
            elif update_type == "reasoning_token":
                # Stream reasoning tokens
                print(update["token"], end="", flush=True)
            
            elif update_type == "plan_complete":
                plan = update["plan"]
                print(f"\n\n✓ Plan created with {len(plan.actions)} actions")
                print("\n📝 Action Plan:")
                
                for i, action in enumerate(plan.actions, 1):
                    print(f"\n  {i}. [{action.skill}] {action.description}")
                    if action.depends_on:
                        print(f"     Dependencies: {', '.join(action.depends_on)}")
        
        # Execution phase
        elif phase == "execution":
            if update_type == "execution_started":
                print(f"\n\n⚙️  TIER 2 & 3: ORCHESTRATOR + SKILLDOCK - Executing plan...")
                print(f"Total actions: {update['total_actions']}")
            
            elif update_type == "level_started":
                print(f"\n📍 Level {update['level']}: {', '.join(update['actions'])}")
            
            elif update_type == "action_started":
                print(f"\n  ⚡ {update['action_id']}: {update['description']}")
                print(f"     Skill: {update['skill']}")
            
            elif update_type == "action_completed":
                print(f"     ✓ Completed in {update['duration']:.2f}s")
                # Show output preview
                output = str(update['output'])[:100]
                print(f"     Output: {output}...")
            
            elif update_type == "action_failed":
                print(f"     ✗ Failed: {update['error']}")
            
            elif update_type == "execution_completed":
                print(f"\n\n{'='*70}")
                if update['success']:
                    print(f"✓ SUCCESS - Completed {update['completed']} actions")
                else:
                    print(f"✗ FAILED - {update['failed']} actions failed")


if __name__ == "__main__":
    asyncio.run(main())
