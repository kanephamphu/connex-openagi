
import asyncio
import os
from agi.config import AGIConfig
from agi.skilldock.skills.general_chat.scripts.agent import GeneralChatSkill

async def test_chat_skill():
    print("Testing GeneralChatSkill...")
    
    # 1. Initialize
    config = AGIConfig.from_env()
    chat_skill = GeneralChatSkill(config)
    print("[PASS] Skill initialized")
    
    # 2. Test Greeting
    print("Test 1: Simple Greeting")
    try:
        reply = await chat_skill.execute("Hello, are you there?")
        print(f"User: Hello, are you there?")
        print(f"AI: {reply.get('reply', 'NO REPLY')}")
        
        if reply.get("reply"):
            print("[PASS] Greeting successful")
        else:
            print("[FAIL] No reply generated")
    except Exception as e:
        print(f"[FAIL] Greeting error: {e}")
        
    # 3. Test Knowledge (Mock response if no API key, but verifies flow)
    print("\nTest 2: Knowledge Question")
    try:
        reply = await chat_skill.execute("Why is the sky blue? Keep it very short.")
        print(f"User: Why is the sky blue?")
        print(f"AI: {reply.get('reply', 'NO REPLY')}")
        
        if reply.get("reply"):
             print("[PASS] Knowledge question successful")
    except Exception as e:
        print(f"[FAIL] Knowledge error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_skill())
