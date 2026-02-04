
import asyncio
from agi import AGI
from agi.config import AGIConfig

async def demo_expansion():
    print("\n" + "="*50)
    print("DEMO: AGENT EXPANSION (Web, Time, Desktop)")
    print("="*50)
    
    config = AGIConfig.from_env()
    config.verbose = True
    
    agi = AGI(config)
    await agi.initialize()
    
    # 1. Test Browser Skill
    print("\n[Skill] Testing Browser Search...")
    browser = agi.skill_registry.get_skill("browser")
    if browser:
        # Mock search due to likely network/library constraints in test env, 
        # but let's try calling it.
        # Note: googlesearch might fail in some headless/IP blocked envs.
        try:
            res = await browser.execute(action="search", query="Connex AGI")
            print(f"Search Results: {res}")
        except Exception as e:
            print(f"Search failed (expected in restrictive env): {e}")
    else:
        print("Browser skill not found.")
        
    # 2. Test Smart Clipboard Reflex
    print("\n[Reflex] Testing Smart Clipboard...")
    # Simulate an event
    event = {
        "type": "clipboard_change",
        "payload": {"content": "https://example.com/article"}
    }
    
    triggered = await agi.reflex.process_event(event)
    if triggered:
        for t in triggered:
            print(f"Reflex Triggered: {t['reflex']}")
            print(f"Plan: {t['plan']}")
    else:
        print("No reflex triggered.")
        
    # 3. Test Scheduler Reflex
    print("\n[Reflex] Testing Scheduler Tick...")
    tick_event = {
        "type": "tick",
        "payload": {"timestamp": 1234567890, "readable": "Tue Feb 4 12:00:00 2026"}
    }
    await agi.reflex.process_event(tick_event)

if __name__ == "__main__":
    asyncio.run(demo_expansion())
