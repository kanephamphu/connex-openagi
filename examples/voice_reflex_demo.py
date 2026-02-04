
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_voice_reflex():
    # 1. Initialize AGI
    config = AGIConfig.from_env()
    config.verbose = True
    agi = AGI(config)
    await agi.initialize()
    
    print("\n" + "="*50)
    print("DEMO: VOICE REFLEX (Listening)")
    print("="*50)
    
    # 2. Get Voice Perception
    voice_perception = agi.perception.get_module("voice_listener")
    if not voice_perception:
        print("Error: Voice Perception module not found/registered!")
        return

    print("Please check your microphone access permissions.")
    print("Listening for 5 seconds... Say something!")
    
    # 3. Perceive: Listen
    result = await voice_perception.perceive(timeout=5)
    
    if result.get("status") != "success":
        print(f"Perception Failed: {result}")
        return

    text = result.get("text")
    print(f"I heard: '{text}'")
    
    # 4. Trigger Reflex
    print("Checking Reflexes...")
    event = {
        "type": "voice_input",
        "payload": result
    }
    
    triggered_plans = await agi.reflex.process_event(event)
    
    if not triggered_plans:
        print("No reflex triggered.")
    else:
        for plan_info in triggered_plans:
            reflex_name = plan_info["reflex"]
            print(f"Reflex '{reflex_name}' triggered!")
            print("Action Plan:", plan_info["plan"])
            
            # 5. Execute Action (Simulation)
            # In a real loop, the Orchestrator would execute this plan.
            # Here we manually check if it was our voice_commander
            if reflex_name == "voice_commander":
                 # Execute the 'Speak' action if present
                 for action in plan_info["plan"]:
                     skill_name = action.get("skill")
                     if skill_name == "speak":
                         speak_skill = agi.skill_registry.get_skill("speak")
                         if speak_skill:
                             await speak_skill.execute(**action.get("inputs", {}))

if __name__ == "__main__":
    asyncio.run(demo_voice_reflex())
