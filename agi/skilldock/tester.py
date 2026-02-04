"""
Skill Tester module.

Uses the GenAI Brain to verify skill behavior against defined test cases.
"""

from typing import Dict, Any, List
from agi.skilldock.base import Skill, SkillTestCase
from agi.brain import GenAIBrain, TaskType
import json

class SkillTester:
    def __init__(self, brain: GenAIBrain):
        self.brain = brain
        
    async def test_skill(self, skill: Skill) -> Dict[str, Any]:
        """
        Run all test cases for a skill.
        """
        report = {
            "skill": skill.metadata.name,
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        if not skill.metadata.tests:
            print(f"[SkillTester] No tests defined for {skill.metadata.name}")
            return report
            
        print(f"\n[TEST] Testing skill: {skill.metadata.name}")
        
        for i, test_case in enumerate(skill.metadata.tests):
            print(f"  Running Case {i+1}: {test_case.description}...")
            
            try:
                # Execute
                result = await skill.execute(**test_case.input)
                
                # Evaluate
                success, reason = await self._evaluate_result(test_case, result)
                
                if success:
                    print(f"  [PASS] PASSED")
                    report["passed"] += 1
                else:
                    print(f"  [FAIL] FAILED: {reason}")
                    report["failed"] += 1
                    
                report["results"].append({
                    "case": test_case.description,
                    "input": test_case.input,
                    "output": result,
                    "success": success,
                    "reason": reason
                })
                
            except Exception as e:
                print(f"  [ERR] ERROR: {e}")
                report["failed"] += 1
                report["results"].append({
                    "case": test_case.description,
                    "input": test_case.input,
                    "error": str(e),
                    "success": False
                })
                
        return report

    async def _evaluate_result(
        self, 
        test_case: SkillTestCase, 
        result: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Evaluate output using exact match or Brain-based assertions.
        """
        # 1. Exact match (if expected_output provided)
        if test_case.expected_output:
            # Check subset match
            for k, v in test_case.expected_output.items():
                if result.get(k) != v:
                    return False, f"Expected {k}={v}, got {result.get(k)}"
                    
        # 2. Brain-based assertions
        if test_case.assertions:
            assertions_text = "\n".join([f"- {a}" for a in test_case.assertions])
            prompt = f"""
            You are a QA Tester. Evaluate this skill execution.
            
            Input: {json.dumps(test_case.input)}
            Output: {json.dumps(result)}
            
            Check these assertions:
            {assertions_text}
            
            Return JSON: {{"passed": bool, "reason": "explanation"}}
            """
            
            provider, model = self.brain.select_model(TaskType.PLANNING)
            client = self.brain.get_client(provider)
            
            try:
                # Call LLM (Pseudo-code for generic client adapter)
                # Adapting to OpenAI-style chat completion for simplicity
                if hasattr(client, "chat"):
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
                    )
                    content = response.choices[0].message.content
                    
                    # cleaner parsing needed
                    clean_content = content.replace("```json", "").replace("```", "").strip()
                    eval_result = json.loads(clean_content)
                    return eval_result.get("passed", False), eval_result.get("reason", "No reason provided")
                else:
                    return False, "Brain client incompatible with tester (requires chat completion)"
                    
            except Exception as e:
                return False, f"Brain evaluation failed: {e}"
                
        return True, "All checks passed"
