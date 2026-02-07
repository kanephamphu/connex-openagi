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

    async def start_background_loop(self):
        """
        Starts the background motivation loop.
        """
        import asyncio
        if self.config.verbose:
            print(f"[Motivation] Starting background loop (Interval: {self.config.motivation_interval}s)")
            
        while True:
            try:
                await asyncio.sleep(self.config.motivation_interval)
                await self.run_skill_review_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Motivation] Error in background loop: {e}")
                await asyncio.sleep(60) # Backoff on error

    async def run_skill_review_cycle(self):
        """
        Review missing skills and attempt recovery.
        """
        if self.config.verbose:
            print("[Motivation] Running Skill Review Cycle...")
            
        from agi.utils.database import DatabaseManager
        db = DatabaseManager()
        pending_requests = db.get_pending_skill_requests(limit=5)
        
        if not pending_requests:
            if self.config.verbose:
                print("[Motivation] No pending skill requests found.")
            return

        # We need access to registry client. 
        # It's not passed in init, but we can instantiate strictly for this purpose
        from agi.utils.registry_client import RegistryClient
        # We also need SkillRegistry to install/create
        # Ideally this should be injected, but for now we might need to rely on the main AGI instance
        # OR we can assume we have access to it via some other way.
        # However, MotivationEngine is initialized in AGI.__init__, so passing registry is cleaner.
        # For now, let's just use the client directly to check remote availability first.
        
        registry_client = RegistryClient(self.config)
        
        for req in pending_requests:
            query = req['query']
            print(f"[Motivation] Reviewing missing skill: '{query}' (Requested {req['count']} times)")
            
            # 1. Search Remote with Criteria
            try:
                results = await registry_client.search("skill", query)
                best_candidate = None
                
                for res in results:
                    rating = res.get("rating", 0)
                    downloads = res.get("downloads", 0)
                    
                    if rating >= self.config.skill_review_min_rating and downloads >= self.config.skill_review_min_downloads:
                        best_candidate = res
                        break
                
                if best_candidate:
                    print(f"[Motivation] Found high-quality remote skill: {best_candidate.get('name')}. Auto-installing...")
                    # We need to trigger installation. 
                    # Since we don't have the registry instance easily here without circular imports or refactoring AGI init,
                    # We will rely on AGI.skill_registry if possible, or re-instantiate.
                    # Re-instantiating Registry is safe as it uses the same DB/Storage.
                    from agi.skilldock.registry import SkillRegistry
                    registry = SkillRegistry(self.config)
                    
                    scoped_name = best_candidate.get("scopedName") or best_candidate.get("name")
                    if await registry.install_skill(scoped_name):
                        db.log_skill_request(query, status="found_remote")
                        print(f"[Motivation] Installed '{scoped_name}' successfully.")
                    else:
                        print(f"[Motivation] Failed to install '{scoped_name}'.")
                else:
                    print(f"[Motivation] No remote skill met criteria (R>{self.config.skill_review_min_rating}, D>{self.config.skill_review_min_downloads}). Triggering Auto-Creation...")
                    # Trigger Creation
                    # We need to run the SkillAcquisition skill.
                    from agi.skilldock.skills.skill_acquisition.scripts.agent import SkillAcquisitionSkill
                    acq_skill = SkillAcquisitionSkill(self.config)
                    
                    result = await acq_skill.execute(requirement=f"Create a skill for: {query}")
                    if result.get("success"):
                        db.log_skill_request(query, status="created")
                        print(f"[Motivation] Auto-created skill for '{query}' successfully.")
                    else:
                        print(f"[Motivation] Auto-creation failed for '{query}': {result.get('message')}")
                        # Don't mark as failed permanently, retry later? Or mark failed.
                        # For now, maybe bump count or leave pending to retry? 
                        # Let's leave pending but maybe we need a 'failed_attempts' counter to avoid infinite loops.
            except Exception as e:
                print(f"[Motivation] Error processing '{query}': {e}")
