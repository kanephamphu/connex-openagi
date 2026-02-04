
import asyncio
import json
from agi import AGI
from agi.config import AGIConfig

async def demo_perception_and_reflex():
    # 1. Initialize AGI with verbose logging to see what's happening
    config = AGIConfig.from_env()
    config.verbose = True
    agi = AGI(config)
    await agi.initialize()
    
    print("\n" + "="*50)
    print("DEMO: PERCEPTION LAYER")
    print("="*50)
    
    # Query the System Monitor perception module
    try:
        perception_data = await agi.perception.perceive("system_monitor")
        print(f"Perceived System Metrics: {json.dumps(perception_data, indent=2)}")
    except Exception as e:
        print(f"Perception failed: {e}")
        
    print("\n" + "="*50)
    print("DEMO: REFLEX LAYER (UNCONDITIONAL RESPONSE)")
    print("="*50)
    
    # Simulate a critical system alert event
    critical_event = {
        "type": "system_alert",
        "payload": {
            "severity": "critical",
            "message": "CPU usage exceeded 90% on node primary-worker-1"
        }
    }
    
    print(f"Processing critical event: {critical_event['payload']['message']}")
    
    # Process through Reflex Layer
    # Returns a list of triggered plans
    triggered_plans = await agi.reflex.process_event(critical_event)
    
    if triggered_plans:
        print(f"Reflex Triggered: {triggered_plans[0]['reflex']}")
        print("Executing instant survival plan via Orchestrator...")
        
        # Execute the first triggered plan
        # We need an actual Plan object or just a list of steps for the orchestrator
        # The Orchestrator expects a Plan object, so let's check how to wrap it.
        # But for this demo, we'll see if we can just trigger it.
        
        # Note: In a real scenario, the AGI instance would handle this mapping.
        # For the demo, let's just show the plan it generated.
        print(f"Generated Plan: {json.dumps(triggered_plans[0]['plan'], indent=2)}")
        
        # To actually execute it, we'd do:
        # from agi.planner.brain_planner import Plan
        # plan = Plan(goal="Auto Recovery", actions=triggered_plans[0]['plan'])
        # await agi.orchestrator.execute_plan(plan)
    else:
        print("No reflex triggered for this event.")

    print("\n" + "="*50)
    print("DEMO: BRAIN REASONING WITH CONSTITUTION")
    print("="*50)
    
    # Show that the brain now considers the constitution and perception
    goal = "Check if the system is overloaded and summarize status"
    print(f"Goal: {goal}")
    
    # We use streaming to see the "Inner Monologue"
    async for update in agi.execute_with_streaming(goal):
        if update.get("type") == "reasoning_token":
            # Just print a few tokens to show it's working
            pass
        elif update.get("phase") == "planning" and update.get("type") == "planning_started":
             print("\nBrain is now reasoning (considering SOUL.md and Perception)...")
        elif update.get("type") == "plan_complete":
             print("\nPlan generated successfully!")
             break

if __name__ == "__main__":
    asyncio.run(demo_perception_and_reflex())
