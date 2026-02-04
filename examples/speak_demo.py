
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_speak_skill():
    # 1. Initialize AGI
    config = AGIConfig.from_env()
    config.verbose = True
    agi = AGI(config)
    await agi.initialize()
    
    print("\n" + "="*50)
    print("DEMO: SPEAK SKILL (Text-to-Speech)")
    print("="*50)
    
    # 2. Get the skill
    speak_skill = agi.skill_registry.get_skill("speak")
    if not speak_skill:
        print("Error: Speak skill not found!")
        return

    # 3. Test Text-to-Speech
    text = "Hello! I am Connex AGI. I can now speak to you using my new voice capabilities."
    print(f"Speaking: '{text}'")
    
    result = await speak_skill.execute(text=text)
    
    if result.get("status") == "success":
        print(f"Success! Audio played from: {result.get('file_path')}")
    else:
        print(f"Failed to speak: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(demo_speak_skill())
