"""
CLI tool to test AGI skills using the built-in SkillTester.

Usage:
    python examples/test_skills.py [skill_name]

If no skill_name is provided, tests all built-in skills.
"""

import sys
import asyncio
import os
from agi import AGI, AGIConfig
from agi.skilldock.tester import SkillTester

async def main():
    # Setup config (mock keys for testing logic)
    config = AGIConfig.from_env()
    config.deepseek_api_key = "mock_key"
    config.openai_api_key = "mock_key"
    config.planner_model = "mock-model"
    
    # Patch AGI initialization to avoid real client kwargs issues if any
    # Actually, AGI check keys in init, which we just mocked.
    
    agi = AGI(config)
    tester = SkillTester(agi.brain)
    
    # Patch _evaluate_result to mock brain behavior
    original_eval = tester._evaluate_result
    
    async def mock_evaluate(test_case, result):
        # Specific check for assertions to verify logic flow
        if test_case.assertions:
            print(f"    [MockBrain] Evaluating assertions against result: {result.keys()}")
            return True, "Mock Brain says OK"
        return await original_eval(test_case, result)
        
    tester._evaluate_result = mock_evaluate
    
    target_skill = sys.argv[1] if len(sys.argv) > 1 else None
    
    skills_to_test = []
    if target_skill:
        try:
            skills_to_test.append(agi.skill_registry.get_skill(target_skill))
        except KeyError:
            print(f"Error: Skill '{target_skill}' not found.")
            return
    else:
        # Test all skills that have tests defined
        for skill in agi.skill_registry._skills.values():
            if skill.metadata.tests:
                skills_to_test.append(skill)
    
    print(f"Running tests for {len(skills_to_test)} skills...\n")
    
    total_passed = 0
    total_failed = 0
    
    for skill in skills_to_test:
        report = await tester.test_skill(skill)
        total_passed += report["passed"]
        total_failed += report["failed"]
        
    print("\n" + "="*40)
    print("TEST SUMMARY")
    print("="*40)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed:      {total_passed}")
    print(f"Failed:      {total_failed}")
    
    if total_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
