
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_identity_dynamic():
    print("\n" + "="*50)
    print("DEMO: IDENTITY DYNAMIC STATE")
    print("="*50)
    
    config = AGIConfig.from_env()
    agi = AGI(config)
    await agi.initialize()
    
    # 1. Set dynamic state
    print("\n[Identity] Setting dynamic state 'mood'='Happy'...")
    agi.identity.set_state("mood", "Happy")
    
    # 2. Get state
    mood = agi.identity.get_state("mood")
    print(f"[Identity] Retrieved 'mood': {mood}")
    
    if mood == "Happy":
        print("PASS: Dynamic state storage working.")
    else:
        print("FAIL: Dynamic state mismatch.")
        
    # 3. Check Prompt injection
    prompt = agi.identity.get_identity_prompt()
    print(f"\n[Identity] Prompt Injection Check:\n---\n{prompt}\n---")
    
    if "'mood': 'Happy'" in prompt:
        print("PASS: Dynamic state injected into prompt.")
    else:
        print("FAIL: Dynamic state missing from prompt.")

if __name__ == "__main__":
    asyncio.run(demo_identity_dynamic())
