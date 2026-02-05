
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def test_init():
    try:
        print("[*] Initializing AGI config...")
        config = AGIConfig.from_env()
        config.verbose = True
        
        print("[*] Initializing AGI instance...")
        # This will trigger the skill registration and the EmotionDetectionSkill instantiation
        agi = AGI(config)
        
        print("[+] AGI initialized successfully!")
    except Exception as e:
        print(f"[-] AGI initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())
