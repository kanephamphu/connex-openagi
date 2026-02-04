"""
Verification test for the Motivation System.
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agi import AGI
from agi.config import AGIConfig

async def test_motivation_system():
    print("\n[Test] Starting Motivation System Verification...\n")
    
    # 1. Setup: Use the existing log file for evaluation
    log_file = "debug_test_final.log"
    if not os.path.exists(log_file):
        print(f"[Test] Creating a mock log file {log_file}...")
        with open(log_file, "w") as f:
            f.write("[Orchestrator] Executing action_1 (web_search)\n")
            f.write("[Test] Action Failed: Rate limit exceeded or skill missing capability for deep PDF analysis\n")
    
    config = AGIConfig.from_env()
    config.verbose = True
    # Ensure it uses our mock/existing log
    config.log_file_path = log_file 
    
    agi = AGI(config)
    await agi.initialize()
    
    # 2. Trigger execution
    # We use a goal that might trigger "skill_acquisition" based on the log failure
    goal = "I need to analyze complex PDF documents which current tools fail at."
    
    print(f"[Test] Goal: {goal}\n")
    print("[Test] Execution Trace:")
    print("-" * 50)
    
    motivation_triggered = False
    improvement_plan_started = False
    
    async for update in agi.execute_with_streaming(goal):
        phase = update.get("phase")
        type = update.get("type")
        
        if phase == "motivation":
            motivation_triggered = True
            if type == "improvement_triggered":
                print(f"\n[Motivation] Improvement Triggered: {update.get('suggestion', {}).get('feedback')}")
            elif type == "action_started":
                improvement_plan_started = True
                print(f"[Motivation] Executing: {update.get('action_id')}")
            elif type == "action_completed":
                print(f"[Motivation] Completed: {update.get('action_id')}")

    print("\n" + "-" * 50)
    
    # 3. Validation
    if motivation_triggered:
        print("\n✅ VERIFICATION PASSED: Mutation System entered the motivation phase.")
    else:
        print("\n❌ VERIFICATION FAILED: Motivation phase was never entered.")

if __name__ == "__main__":
    asyncio.run(test_motivation_system())
