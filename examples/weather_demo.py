
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_weather():
    print("\n" + "="*50)
    print("DEMO: WEATHER MODULE (Skill, Perception, Reflex)")
    print("="*50)
    
    config = AGIConfig.from_env()
    config.verbose = True
    
    agi = AGI(config)
    await agi.initialize()
    
    # 1. Test Weather Skill
    print("\n[Skill] Testing Weather Check for London...")
    weather_skill = agi.skill_registry.get_skill("weather")
    if weather_skill:
        try:
            res = await weather_skill.execute(city="London")
            print(f"Result: {res}")
        except Exception as e:
            print(f"Weather check failed: {e}")
    else:
        print("Weather skill not found.")
        
    # 2. Test Weather Alert Reflex (Simulated Event)
    print("\n[Reflex] Testing Weather Alert...")
    # Simulate a sudden change to Rain (Code 61)
    event = {
        "type": "weather_change",
        "payload": {
            "old_code": 0, # Clear
            "new_code": 61, # Rain
            "temp": 15.5
        }
    }
    
    triggered = await agi.reflex.process_event(event)
    if triggered:
        for t in triggered:
            print(f"Reflex Triggered: {t['reflex']}")
            print(f"Plan: {t['plan']}")
    else:
        print("No reflex triggered.")

if __name__ == "__main__":
    asyncio.run(demo_weather())
