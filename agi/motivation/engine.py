"""
Motivation Engine: The core of the AGI's drive for improvement.
"""

from typing import List, Dict, Any, Optional
from agi.motivation.log_reader import LogReader
from agi.motivation.evaluator import Evaluator
from agi.motivation.curiosity import CuriosityModule
from agi.brain import GenAIBrain

class MotivationEngine:
    """
    Coordinates self-evaluation and improvement actions.
    """
    
    def __init__(self, config, brain: GenAIBrain):
        self.config = config
        self.brain = brain
        self.log_reader = LogReader(config.log_file_path if hasattr(config, "log_file_path") else "debug_test.log")
        self.evaluator = Evaluator(brain)
        self.curiosity = CuriosityModule(config, brain)
        
    async def review_performance(self, current_goal: str) -> Optional[Dict[str, Any]]:
        """
        Reviews recent logs and evaluates performance against the current goal.
        Returns improvement suggestions if needed.
        """
        if self.config.verbose:
            print("[Motivation] Reviewing recent performance...")
            
        log_content = self.log_reader.read_recent_trace()
        if not log_content:
            return None
            
        actions = self.log_reader.extract_actions(log_content)
        evaluation = await self.evaluator.evaluate_performance(current_goal, actions)
        
        if self.config.verbose:
            print(f"[Motivation] Evaluation Result: {evaluation.get('feedback')} (Score: {evaluation.get('score')})")
            
        return evaluation if evaluation.get("needs_improvement") else None

    async def generate_improvement_plan(self, evaluation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Converts an evaluation result into a concrete improvement plan (e.g., a new DAG).
        """
        # Determine improvement type from nested 'analysis' or top-level (fallback)
        analysis = evaluation.get("analysis", {})
        imp_type = analysis.get("improvement_type") or evaluation.get("improvement_type")
        action = analysis.get("suggested_action") or evaluation.get("suggested_action")
        
        if imp_type == "skill_acquisition":
            return {
                "id": "motivation_skill_acquisition",
                "skill": "skill_acquisition",
                "description": f"Acquire new capability: {action}",
                "inputs": {
                    "requirement": action
                }
            }
        return None

    async def propose_curiosity_goal(self) -> Optional[Dict[str, Any]]:
        """
        Proposes an intrinsic goal to pursue when idle.
        """
        if self.config.verbose:
            print("[Motivation] Pondering intrinsic goals (Curiosity)...")
        return await self.curiosity.propose_goal()
