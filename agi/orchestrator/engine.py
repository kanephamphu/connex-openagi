"""
Core orchestration engine.

Executes action plans step-by-step with proper state management and error handling.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agi.orchestrator.state import ExecutionState, StepResult
from agi.orchestrator.mapper import IOMapper
from agi.planner.base import ActionPlan
from agi.skilldock.base import MissingConfigError


from agi.orchestrator.corrector import Corrector

@dataclass
class ExecutionResult:
    """Result from executing an entire plan."""
    
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    trace: List[StepResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    state: Optional[ExecutionState] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "trace": [s.to_dict() for s in self.trace],
            "errors": self.errors,
            "duration": self.duration,
        }


class Orchestrator:
    """
    Orchestrates execution of action plans.
    
    Manages state, routes actions to skills, and handles errors.
    """
    
    def __init__(self, config, skill_registry):
        """
        Initialize the orchestrator.
        
        Args:
            config: AGIConfig instance
            skill_registry: SkillRegistry instance
        """
        self.config = config
        self.skill_registry = skill_registry
        self.mapper = IOMapper()
        self.corrector = Corrector(config)
    
    async def execute_plan(self, plan: ActionPlan) -> ExecutionResult:
        """
        Execute an action plan.
        
        Args:
            plan: ActionPlan to execute
            
        Returns:
            ExecutionResult with outputs and execution trace
        """
        start_time = time.time()
        state = ExecutionState()
        
        # Get execution order (topological sort)
        execution_levels = plan.get_execution_order()
        
        if self.config.verbose:
            print(f"\n[Orchestrator] Executing plan with {len(plan.actions)} actions")
            print(f"[Orchestrator] Execution levels: {execution_levels}")
        
        # Initialize pending actions
        state.pending = [a.id for a in plan.actions]
        
        try:
            # Execute level by level
            for level_idx, level_actions in enumerate(execution_levels):
                if self.config.verbose:
                    print(f"\n[Orchestrator] Level {level_idx + 1}: {level_actions}")
                
                # Execute actions in this level (can run in parallel)
                level_tasks = []
                for action_id in level_actions:
                    action = next(a for a in plan.actions if a.id == action_id)
                    level_tasks.append(self._execute_action(action, state))
                
                # Wait for all actions in this level to complete
                level_results = await asyncio.gather(*level_tasks, return_exceptions=True)
                
                # Process results
                for action_id, result in zip(level_actions, level_results):
                    # Check for exceptions (system errors) or failed results (skill errors)
                    is_failure = isinstance(result, Exception) or (isinstance(result, StepResult) and not result.success)
                    
                    if is_failure:
                        # Normalize error info
                        error_msg = str(result) if isinstance(result, Exception) else result.error
                        failed_inputs = {}
                        if isinstance(result, StepResult) and result.metadata:
                            failed_inputs = result.metadata.get("inputs", {})
                        
                        if self.config.verbose:
                            # CancelledError has no string representation often
                            if isinstance(result, asyncio.CancelledError):
                                error_msg = "Task was cancelled (likely a timeout)"
                            else:
                                error_msg = str(result) if isinstance(result, Exception) else result.error
                                
                            print(f"[Orchestrator] Action {action_id} failed: {error_msg}")
                        
                        # --- SELF CORRECTION ---
                        repaired = False
                        if self.config.self_correction_enabled and failed_inputs:
                            # Attempt fast fix
                            action = next(a for a in plan.actions if a.id == action_id)
                            
                            if self.config.verbose: 
                                print(f"[Orchestrator] Attempting immune system fix for {action.skill}...")
                            
                            fixed_inputs = await self.corrector.correct(
                                skill_name=action.skill,
                                original_inputs=failed_inputs,
                                error_message=error_msg
                            )
                            
                            if fixed_inputs:
                                if self.config.verbose:
                                    print(f"[Orchestrator] Fix proposed: {fixed_inputs}")
                                    print(f"[Orchestrator] Retrying action {action_id}...")
                                
                                # Retry with fixed inputs (bypass standard execution wrapper to inject inputs)
                                try:
                                    skill = self.skill_registry.get_skill(action.skill)
                                    
                                    # Sanitize fixed_inputs: only keep keys defined in skill's input schema
                                    # or allow standard ones if schema is loose.
                                    input_schema = skill.metadata.input_schema
                                    valid_keys = []
                                    if isinstance(input_schema, dict):
                                        valid_keys = list(input_schema.get("properties", {}).keys())
                                        if not valid_keys and "type" not in input_schema:
                                            valid_keys = list(input_schema.keys())
                                            
                                    sanitized_inputs = fixed_inputs
                                    if valid_keys:
                                        sanitized_inputs = {k: v for k, v in fixed_inputs.items() if k in valid_keys}
                                    
                                    if self.config.verbose and sanitized_inputs != fixed_inputs:
                                        print(f"[Orchestrator] Sanitized inputs for retry: {sanitized_inputs}")

                                    # Execute with timeout
                                    output = await asyncio.wait_for(
                                        skill.execute(**sanitized_inputs),
                                        timeout=action.metadata.get("timeout", self.config.action_timeout)
                                    )
                                    
                                    if action.output_schema:
                                        self.mapper.validate_output(output, action.output_schema)
                                        
                                    # Success! Replace the failed result
                                    result = StepResult(
                                        action_id=action.id,
                                        success=True,
                                        output=output,
                                        duration=0.0, # Approximate
                                        metadata={"skill": action.skill, "inputs": fixed_inputs, "corrected": True}
                                    )
                                    repaired = True
                                    print(f"[Orchestrator] Action {action_id} repaired successfully! ✅")
                                except Exception as e_retry:
                                    print(f"[Orchestrator] Retry failed: {e_retry}")
                                    # Fall through to standard failure
                        
                        # Check again if repaired
                        if repaired:
                             state.mark_completed(action_id, result)
                             if self.config.verbose:
                                output_preview = self.mapper.format_output_for_display(result.output, 100)
                                print(f"[Orchestrator] Action {action_id} completed (after fix): {output_preview}")
                        else:
                            # --- STANDARD FAILURE HANDLING (Replan or Abort) ---
                            step_result = result if isinstance(result, StepResult) else StepResult(action_id, False, str(result))
                            state.mark_failed(action_id, step_result)
                            
                            # Get action node to check priority
                            try:
                                action = next(a for a in plan.actions if a.id == action_id)
                            except StopIteration:
                                # Should not happen
                                raise Exception(error_msg)
                                
                            priority = getattr(action, "priority", "MAJOR")
                            
                            if priority == "MAJOR":
                                if self.config.self_correction_enabled:
                                    # Fallback to heavy replan
                                    try:
                                        return await self._handle_failure(plan, state, action_id, error_msg)
                                    except Exception as replan_err:
                                         raise Exception(f"MAJOR step '{action_id}' failed and replan failed: {error_msg}. (Replan error: {replan_err})")
                                else:
                                    raise Exception(f"MAJOR step '{action_id}' failed: {error_msg}")
                            elif priority == "SKIPPABLE":
                                if self.config.verbose:
                                    print(f"[Orchestrator] SKIPPABLE step '{action_id}' failed/skipped. No impact on goal. Error: {error_msg}")
                                continue
                            else: # MINOR
                                if self.config.verbose or True: # Always log minor failures for now
                                    print(f"[Orchestrator] MINOR step '{action_id}' failed. Continuing remaining independent actions. Error: {error_msg}")
                                # Just continue the loop - dependencies of this minor step will be skipped automatically
                                continue

                    else:
                        # Action succeeded
                        state.mark_completed(action_id, result)
                        if self.config.verbose:
                            output_preview = self.mapper.format_output_for_display(result.output, 100)
                            print(f"[Orchestrator] Action {action_id} completed: {output_preview}")
            
            # Execution complete
            state.ended_at = datetime.now()
            duration = time.time() - start_time
            
            # Get final output (from last action)
            final_output = {}
            if state.completed:
                last_action_id = state.completed[-1]
                final_output = state.results[last_action_id].output
            
            if self.config.verbose:
                print(f"\n[Orchestrator] Plan execution completed in {duration:.2f}s")
            
            return ExecutionResult(
                success=True,
                output=final_output,
                trace=[state.results[aid] for aid in state.completed],
                duration=duration,
                state=state
            )
        
        except Exception as e:
            # Unexpected error
            state.ended_at = datetime.now()
            duration = time.time() - start_time
            
            if self.config.verbose:
                err_str = str(e) or e.__class__.__name__
                print(f"[Orchestrator] Execution failed: {err_str}")
            
            return ExecutionResult(
                success=False,
                errors=[str(e)],
                trace=[state.results[aid] for aid in state.completed],
                duration=duration,
                state=state
            )

    async def prepare_repair_plan(self, failed_goal: str, failed_action_id: str, error_msg: str, completed_actions: list) -> Any:
        # Import planner
        from agi.planner.brain_planner import BrainPlanner
        import inspect

        # Try to identify skill source
        skill_file_path = None
        
        # NOTE: Caller must inject "skill_file_path" into context!
        planner = BrainPlanner(self.config)
        
        # We just return the planner generator
        return planner.create_plan_streaming(
            goal=f"Fix failure in previous step '{failed_action_id}': {error_msg}. Resume goal: {failed_goal}",
            context={
                "completed_actions": completed_actions,
                "failed_action": failed_action_id,
                "error": error_msg
            }
        )
    
    async def _execute_action(self, action, state: ExecutionState) -> StepResult:
        """
        Execute a single action.
        
        Args:
            action: ActionNode to execute
            state: Current execution state
            
        Returns:
            StepResult
        """
        start_time = time.time()
        inputs = {}
        
        try:
            # Resolve inputs (with smart remapping)
            # We get the skill first to allow mapper to use its schema
            skill = self.skill_registry.get_skill(action.skill)
            inputs = self.mapper.resolve_inputs(action, state, skill)
            
            if self.config.verbose:
                print(f"[Orchestrator] Executing {action.id} ({action.skill})")
            
            # Check if enabled
            if isinstance(skill.config, dict):
                 if not skill.config.get("enabled", True):
                     raise Exception(f"Skill '{action.skill}' is disabled by the user.")
            
            # Check for missing config
            try:
                await skill.check_config()
            except MissingConfigError as e:
                # Rethrow to be caught by streaming or handle loop
                raise e
            
            # NEW: Validate inputs according to metadata schema
            try:
                await skill.validate_inputs(**inputs)
            except Exception as v_err:
                 raise Exception(f"Input validation failed for '{action.skill}': {v_err}")
            
            # Execute with timeout
            try:
                output = await asyncio.wait_for(
                    skill.execute(**inputs),
                    timeout=action.metadata.get("timeout", self.config.action_timeout)
                )
            except asyncio.TimeoutError:
                raise Exception(f"Action '{action.id}' timed out after {action.metadata.get('timeout', self.config.action_timeout)}s")
            except asyncio.CancelledError:
                # Re-raise so orchestrator knows it was a cancellation
                raise
            
            # Smart Validate & Map output
            if action.output_schema:
                output = self.mapper.validate_output(output, action.output_schema, action.id)
            
            # If skill returned explicit success=False, treat as execution error
            if isinstance(output, dict) and output.get("success") is False:
                error_msg = output.get("message") or output.get("error") or "Skill reports failure without message"
                raise Exception(error_msg)
            
            duration = time.time() - start_time
            
            return StepResult(
                action_id=action.id,
                success=True,
                output=output,
                duration=duration,
                metadata={
                    "skill": action.skill,
                    "inputs": inputs,
                }
            )
        
        except Exception as e:
            duration = time.time() - start_time
            return StepResult(
                action_id=action.id,
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "skill": action.skill,
                    "inputs": inputs, # Capture inputs on failure
                }
            )
    
    async def _handle_failure(
        self,
        plan: ActionPlan,
        state: ExecutionState,
        failed_action: str,
        error: str
    ) -> ExecutionResult:
        """
        Handle action failure with self-correction.
        
        Args:
            plan: Original plan
            state: Current state
            failed_action: ID of failed action
            error: Error message
            
        Returns:
            ExecutionResult after replanning
        """
        if self.config.verbose:
            print(f"\n[Orchestrator] Self-correction: Replanning after failure at {failed_action}")
        
        # Import planner (circular dependency workaround)
        from agi.planner import Planner
        import inspect

        # Try to get skill source path to enable self-repair
        skill_file_path = None
        try:
            # Find the skill involved in the failure
            action = next(a for a in plan.actions if a.id == failed_action)
            skill = self.skill_registry.get_skill(action.skill)
            skill_file_path = inspect.getfile(skill.__class__)
            if self.config.verbose:
                print(f"[Orchestrator] Identified failing skill source: {skill_file_path}")
        except Exception:
            pass

        planner = Planner(self.config)
        
        # Build enhanced context with file path
        context_extras = {"skill_file_path": skill_file_path} if skill_file_path else {}

        # Get relevant skills for the new goal
        skills = await self.skill_registry.get_relevant_skills(plan.goal)

        # Create new plan for remaining work
        new_plan = await planner.replan(
            original_plan=plan,
            failed_step=failed_action,
            error=error,
            completed_steps=state.completed,
            skills=skills,
            **context_extras
        )
        
        # Execute new plan
        return await self.execute_plan(new_plan)
    
    async def execute_plan_streaming(self, plan: ActionPlan):
        """
        Execute plan with streaming progress updates.
        
        Args:
            plan: ActionPlan to execute
            
        Yields:
            Progress dictionaries
        """
        state = ExecutionState()
        execution_levels = plan.get_execution_order()
        
        yield {
            "type": "execution_started",
            "total_actions": len(plan.actions),
            "levels": len(execution_levels)
        }
        
        for level_idx, level_actions in enumerate(execution_levels):
            yield {
                "type": "level_started",
                "level": level_idx + 1,
                "actions": level_actions
            }
            
            # Execute actions
            for action_id in level_actions:
                action = next(a for a in plan.actions if a.id == action_id)
                
                yield {
                    "type": "action_started",
                    "action_id": action_id,
                    "skill": action.skill,
                    "description": action.description
                }
                
                try:
                    result = await self._execute_action(action, state)
                    
                    if result.success:
                        state.mark_completed(action_id, result)
                        yield {
                            "type": "action_completed",
                            "action_id": action_id,
                            "output": result.output,
                            "duration": result.duration
                        }
                    else:
                        state.mark_failed(action_id, result)
                        yield {
                            "type": "action_failed",
                            "action_id": action_id,
                            "error": result.error
                        }
                except MissingConfigError as e:
                    yield {
                        "type": "config_required",
                        "skill": e.skill_name,
                        "missing_keys": e.missing_keys,
                        "schema": e.schema
                    }
                    return

            # --- SELF CORRECTION CHECK ---
            if state.failed:
                # Get the first failure
                failed_id = state.failed[0]
                error_msg = state.results[failed_id].error
                
                if self.config.self_correction_enabled:
                    # UPDATED: Do NOT auto-trigger. Notify user of failure (via history) to allow manual usage.
                    # We just yield the failure and stop.
                    # The frontend will show 'Repair' button which calls trigger_repair()
                    pass
                    
                    # Original Auto-logic (disabled per user request):
                    # yield {
                    #     "type": "correction_started",
                    #     "failed_action": failed_id,
                    #     "error": error_msg
                    # }
                    # ... (rest commented out)
                    
                    return # Stop execution on failure
        
        yield {
            "type": "execution_completed",
            "success": len(state.failed) == 0,
            "completed": len(state.completed),
            "failed": len(state.failed)
        }
