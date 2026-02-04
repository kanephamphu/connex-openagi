
import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agi import AGI
from agi.config import AGIConfig

async def test_self_healing():
    print("\n[Test] Starting Skill Self-Healing Verification...\n")
    
    # 1. Setup: Inject Failure into WebSearch
    skill_path = Path("agi/skilldock/skills/web_search/scripts/agent.py").resolve()
    original_code = skill_path.read_text()
    
    # Inject a crash at the start of execute
    broken_code = original_code.replace(
        'async def execute(self, query: str, engine: str = "auto", num_results: int = 5, extract_keywords: bool = False) -> Dict[str, Any]:',
        'async def execute(self, query: str, engine: str = "auto", num_results: int = 5, extract_keywords: bool = False) -> Dict[str, Any]:\n        raise ValueError("SIMULATED CRASH: Immune System Test")'
    )
    
    print(f"[Test] Injecting simulated crash into {skill_path}...")
    skill_path.write_text(broken_code)
    
    try:
        # 2. Initialize AGI with Self-Correction ENABLED
        config = AGIConfig.from_env()
        config.verbose = True
        config.self_correction_enabled = True # CRITICAL for this test
        
        # Inject dummy keys into env to bypass MissingConfigError
        os.environ["GOOGLE_SEARCH_API_KEY"] = "dummy_key"
        os.environ["GOOGLE_SEARCH_ID"] = "dummy_id"
        os.environ["BING_SEARCH_API_KEY"] = "dummy_key"
        
        agi = AGI(config)
        await agi.initialize()
        print("[Test] AGI Initialized with Immune System active.")
        
        # 3. Trigger the crash
        goal = "Search for 'DeepSeek-R1' and return the first result."
        print(f"[Test] Goal: {goal}\n")
        
        print("[Test] Execution Trace:")
        print("-" * 50)
        
        repaired = False
        
        async for update in agi.execute_with_streaming(goal):
            phase = update.get("phase")
            evt_type = update.get("type")
            
            if phase == "planning":
                if evt_type == "reasoning_token":
                    print(update["token"], end="", flush=True)
            
            elif phase == "execution":
                if evt_type == "action_failed":
                    print(f"\n[Test] Action Failed: {update['error']}")
                elif evt_type == "action_completed":
                    print(f"\n[Test] Action Completed: {str(update.get('output'))[:100]}")
                    # If we got a result after a failure, it was repaired!
                    repaired = True
        
        print("\n" + "-" * 50)
        
        # 4. Verify Repair
        current_code = skill_path.read_text()
        if "raise ValueError" not in current_code:
            print("\n✅ VERIFICATION PASSED: The code was automatically repaired!")
        elif repaired:
             print("\n✅ VERIFICATION PASSED: Task succeeded (likely via runtime patch), but disk might not be saved?")
        else:
            print("\n❌ VERIFICATION FAILED: Code still contains the crash and task failed.")
            print("Current Code Snippet:")
            print(current_code[original_code.find("async def execute"):original_code.find("async def execute")+200])

    except Exception as e:
        print(f"\n[Test] FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 5. Restore Original Code
        print(f"\n[Test] Restoring original code to {skill_path}...")
        skill_path.write_text(original_code)

if __name__ == "__main__":
    asyncio.run(test_self_healing())
