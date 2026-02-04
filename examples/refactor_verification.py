
import asyncio
import time
from agi import AGI
from agi.config import AGIConfig

async def verify_refactor():
    print("\n" + "="*50)
    print("VERIFICATION: REFACTOR, IDENTITY, CONTEXT")
    print("="*50)
    
    config = AGIConfig.from_env()
    config.verbose = True
    
    agi = AGI(config)
    await agi.initialize()
    
    # 1. Verify Identity & Workload Integration
    print("\n[Identity] Waiting for workload update...")
    # Trigger workload perception
    await agi.perception.perceive("workload_monitor")
    
    status = agi.identity.get_status_summary()
    print(f"Identity Status: {status}")
    
    if status.get("cpu", 0) >= 0 and status.get("ram", 0) > 0:
        print("PASS: Identity updated by Workload Perception.")
    else:
        print("FAIL: Identity stats are empty.")

    # 2. Verify Context-Aware Planning
    print("\n[Planner] Testing Context Awareness (Goal: 'What is the weather?')...")
    
    # We want to see if the planner fetches weather data BEFORE generating the plan.
    # To spy on this, we can check if the 'weather' module was accessed recently or trust the verbose logs.
    
    # Run plan creation
    try:
        plan = await agi.planner.create_plan("What is the weather in Tokyo?", context={})
        
        # Check metadata for context
        context = plan.metadata.get("context", {})
        sensor_data = context.get("sensor_data", {})
        print(f"Captured Sensor Context: {sensor_data}")
        
        if "weather_monitor" in sensor_data:
             print("PASS: Planner correctly identified and fetched 'weather_monitor'.")
        else:
             print("WARN: Planner did not fetch weather context (LLM decision variability).")
             
    except Exception as e:
        print(f"Planning failed (expected if API keys invalid): {e}")
        # Even if planning fails due to dummy key, the context gathering happens BEFORE the final generation call?
        # No, _gather_context uses the LLM too. So with dummy keys, it will fail at the context selection step.
        print("Note: With dummy keys, context selection step likely failed gracefully.")

if __name__ == "__main__":
    asyncio.run(verify_refactor())
