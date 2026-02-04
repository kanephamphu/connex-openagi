
import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agi import AGI
from agi.config import AGIConfig

async def test_autonomous_research():
    print("\n[Test] Starting Autonomous Research Verification...\n")
    
    # 1. Initialize AGI
    config = AGIConfig.from_env()
    # Force verbal output for debugging
    config.verbose = True 
    
    agi = AGI(config)
    await agi.initialize()
    print("[Test] AGI Initialized.")
    
    # 2. Define a complex goal that requires multiple steps
    goal = """
    Research the latest advancements in 'Reasoning Models' (like DeepSeek-R1 or OpenAI o1) from 2025-2026.
    Summarize the key findings into a short markdown report.
    Save the report to 'research_report.md'.
    """
    
    print(f"[Test] Goal: {goal}\n")
    
    # 3. Execute with streaming to capture the full thought process
    print("[Test] Execution Trace:")
    print("-" * 50)
    
    final_output = None
    
    try:
        async for update in agi.execute_with_streaming(goal):
            phase = update.get("phase")
            evt_type = update.get("type")
            
            if phase == "planning":
                if evt_type == "reasoning_token":
                    print(update["token"], end="", flush=True)
                elif evt_type == "plan_complete":
                     print(f"\n\n[Test] Plan Created: {len(update['plan']['actions'])} actions.")
            
            elif phase == "execution":
                if evt_type == "action_started":
                    print(f"\n\n[Test] Action: {update['skill']} ({update['description']})")
                elif evt_type == "action_completed":
                    print(f"[Test] Result: {str(update['output'])[:100]}...")
                elif evt_type == "execution_completed":
                    print("\n[Test] Execution Sequence Finished.")
    
    except Exception as e:
        print(f"\n[Test] FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Verify Output
    report_path = Path("research_report.md")
    if report_path.exists():
        content = report_path.read_text()
        print(f"\n[Test] Report Generated Successfully ({len(content)} bytes).")
        print("\n[Test] Preview:\n")
        print(content[:500] + "...")
        print("-" * 50)
        print("\n✅ VERIFICATION PASSED: AGI acted autonomously.")
    else:
        print("\n❌ VERIFICATION FAILED: Report file not found.")

if __name__ == "__main__":
    asyncio.run(test_autonomous_research())
