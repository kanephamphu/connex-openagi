
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Fake required classes for standalone testing if needed, or import real ones
from agi.config import AGIConfig
from agi.orchestrator.engine import Orchestrator
from agi.skilldock.registry import SkillRegistry
from agi.planner.base import ActionPlan, ActionNode

async def test_correction():
    print("Testing Immune System (Self-Correction)...")
    
    # 1. Setup
    config = AGIConfig.from_env()
    config.self_correction_enabled = True
    config.verbose = True # We want to see the logs
    
    registry = SkillRegistry(config)
    registry._load_builtin_skills() # Load code_executor
    
    orch = Orchestrator(config, registry)
    
    # 2. Create a BROKEN plan
    # Syntax Error: Missing closing parenthesis
    broken_code = "print('Hello World'" 
    
    action = ActionNode(
        id="step_1",
        skill="code_executor",
        description="Run broken code",
        inputs={"code": broken_code},
        output_schema={"result": "Any"}
    )
    
    plan = ActionPlan(
        goal="Run code test",
        actions=[action],
        reasoning="Test if invalid code is fixed."
    )
    
    print("\n--- Executing Broken Plan ---")
    print(f"Original Input: {broken_code}")
    
    # 3. Execute
    result = await orch.execute_plan(plan)
    
    # 4. Verify
    print("\n--- Result Analysis ---")
    if result.success:
        print("[PASS] Plan Execution Succeeded!")
        
        # Check trace
        step = result.trace[0]
        if step.metadata.get("corrected"):
            print("[PASS] Correction flag found.")
            print(f"Original Inputs: {step.metadata['inputs']}") 
            # Note: My implementation overrides the metadata['inputs'] with the NEW inputs on success!
            # Let's check output
            print(f"Output: {step.output}")
        else:
            print("[FAIL] Plan succeeded but 'corrected' flag missing?")
    else:
        print("[FAIL] Plan Execution Failed.")
        print(f"Errors: {result.errors}")

if __name__ == "__main__":
    asyncio.run(test_correction())
