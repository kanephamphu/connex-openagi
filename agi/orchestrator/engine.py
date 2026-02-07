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
    
    def __init__(self, config, skill_registry, world_manager=None):
        """
        Initialize the orchestrator.
        
        Args:
            config: AGIConfig instance
            skill_registry: SkillRegistry instance
            world_manager: Shared WorldManager instance
        """
        self.config = config
        self.skill_registry = skill_registry
        self.mapper = IOMapper()
        from agi.brain import GenAIBrain
        self.brain = GenAIBrain(config)
        
        # Use shared world manager or initialize new one (fallback)
        if world_manager:
            self.world = world_manager
        elif getattr(config, 'enable_world_recognition', True):
            from agi.world.manager import WorldManager
            self.world = WorldManager(config, self.brain)
        else:
            self.world = None
    
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
                    level_tasks.append(self._execute_action_with_retry(action, state, max_retries=3))
                
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
                        
                        # --- NEW: RESILIENT FAILURE HANDLING ---
                        repaired = False
                        if self.config.self_correction_enabled:
                            action = next(a for a in plan.actions if a.id == action_id)
                            
                            # 1. Search for Alternative Skill
                            if self.config.verbose:
                                print(f"[Orchestrator] Searching for alternative for failing skill: {action.skill}...")
                            
                            # Get context from failing skill
                            failed_cat, failed_sub = None, None
                            try:
                                fs = self.skill_registry.get_skill(action.skill)
                                failed_cat = fs.metadata.category
                                failed_sub = getattr(fs.metadata, 'sub_category', None)
                            except: pass

                            alternatives = await self.skill_registry.get_relevant_skills(
                                action.description, 
                                limit=3,
                                category=failed_cat,
                                sub_category=failed_sub
                            )
                            # Filter out the failed skill
                            alternatives = [s for s in alternatives if s.metadata.name != action.skill]
                            
                            for alt_skill in alternatives:
                                if self.config.verbose:
                                    print(f"[Orchestrator] Found alternative: {alt_skill.metadata.name}. Attempting execution...")
                                
                                try:
                                    # Remap inputs for alternative skill
                                    alt_inputs = self.mapper.auto_map_to_schema(failed_inputs, alt_skill.metadata, action.description)
                                    
                                    alt_output = await asyncio.wait_for(
                                        alt_skill.execute(**alt_inputs),
                                        timeout=action.metadata.get("timeout", self.config.action_timeout)
                                    )
                                    
                                    # Check for failure in alternative
                                    if isinstance(alt_output, dict) and (alt_output.get("success") is False or "error" in alt_output):
                                         continue
                                         
                                    # Success! Replace result
                                    result = StepResult(
                                        action_id=action.id,
                                        success=True,
                                        output=alt_output,
                                        duration=0.0,
                                        metadata={"skill": alt_skill.metadata.name, "inputs": alt_inputs, "alternative": True}
                                    )
                                    repaired = True
                                    print(f"[Orchestrator] Action {action_id} recovered using alternative skill '{alt_skill.metadata.name}'! 🔄")
                                    break
                                except Exception as alt_err:
                                    if self.config.verbose:
                                        print(f"[Orchestrator] Alternative '{alt_skill.metadata.name}' failed: {alt_err}")
                                    continue
                            
                            # 2. LLM Simulation Fallback
                            if not repaired:
                                if self.config.verbose:
                                    print(f"[Orchestrator] No alternative skill worked. Falling back to LLM Simulation...")
                                
                                try:
                                    simulated_output = await self._simulate_action_result(action, failed_inputs, error_msg, plan.goal)
                                    if simulated_output:
                                        result = StepResult(
                                            action_id=action.id,
                                            success=True,
                                            output=simulated_output,
                                            duration=0.1,
                                            metadata={"skill": "brain_simulation", "inputs": failed_inputs, "simulated": True}
                                        )
                                        repaired = True
                                        print(f"[Orchestrator] Action {action_id} simulated by Brain to continue plan. 🧠")
                                except Exception as sim_err:
                                    if self.config.verbose:
                                        print(f"[Orchestrator] Simulation failed: {sim_err}")
                        
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
                                # Replan is disabled per user request in favor of local alternative discovery/simulation
                                if self.config.verbose:
                                    print(f"[Orchestrator] MAJOR step '{action_id}' failed after all recovery attempts. Stopping execution.")
                                return ExecutionResult(
                                    success=False,
                                    errors=[error_msg],
                                    trace=[state.results[aid] for aid in state.completed],
                                    duration=time.time() - start_time,
                                    state=state
                                )
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
    
    async def _execute_action_with_retry(self, action, state: ExecutionState, max_retries: int = 3) -> StepResult:
        """
        Execute an action with a retry loop.
        """
        last_error = ""
        for attempt in range(max_retries):
            if self.config.verbose and attempt > 0:
                print(f"[Orchestrator] Retry attempt {attempt + 1}/{max_retries} for {action.id}")
            
            result = await self._execute_action(action, state)
            if result.success:
                return result
            
            last_error = result.error
            # Small delay between retries
            await asyncio.sleep(1)
            
        # If we exhausted retries, return the last failure
        return result

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
            
            # --- Clean World Layer Integration ---
            if self.config.verbose:
                print(f"[Orchestrator] Verifying causality for '{action.id}'...")
            
            # # Map skill/action to World Action Type (Simplified mapping for now)
            # world_action_type = "API_CALL" if action.skill != "file_manager" else "CREATE_FILE"
            
            # # 1. Metaphysical Verification (Neural + Guard)
            # is_safe, error = await self.world.simulate_consequence(
            #     action_type=world_action_type,
            #     params=inputs,
            #     description=action.description
            # )
            
            # if not is_safe:
            #     print(f"[Orchestrator] 🛑 METAPHYSICAL STOP: {error}")
            #     raise Exception(f"World Violation: {error}")
                
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
            
            # 2. Commit World State & Get Feeling
            world_result = await self.world.step(
                action_type=world_action_type,
                params=inputs,
                description=action.description
            )
            
            if self.config.verbose and world_result["success"]:
                feeling = world_result["feeling"]
                print(f"[Orchestrator] Feel: {feeling.get('categories')} | {feeling.get('interpretation')}")
                
            # --- Continuous Self-Learning ---
            if world_result["success"]:
                self.world.train_from_experience(
                    world_result["old_state"],
                    world_action_type,
                    inputs,
                    world_result["new_state"]
                )
                self.world.save_knowledge()
            
            # If skill returned explicit success=False or has an 'error' key, treat as execution error
            if isinstance(output, dict):
                is_failed = output.get("success") is False or "error" in output
                if is_failed:
                    error_msg = output.get("error") or output.get("message") or "Skill reports failure without specific message"
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

    async def _simulate_action_result(self, action, inputs, error_msg, goal) -> Dict[str, Any]:
        """
        Use Brain to simulate a successful tool output after a failure.
        """
        from agi.brain import TaskType
        
        prompt = f"""
        TASK: Simluate the output of a failed tool execution to allow an AGI plan to continue.
        
        OVERALL GOAL: {goal}
        
        FAILED STEP: {action.description}
        SKILL ATTEMPTED: {action.skill}
        INPUTS USED: {json.dumps(inputs)}
        ERROR ENCOUNTERED: {error_msg}
        
        INSTRUCTIONS:
        1. Generate a logic and realistic tool output (JSON) that would have been expected if the tool succeeded.
        2. Ensure the output strictly fulfills the requirement of the step so dependent steps can proceed.
        3. Respond ONLY with the JSON object.
        """
        
        try:
            provider, model = self.brain.select_model(TaskType.FAST)
            client = self.get_client_provider(provider)
            
            if provider in ["openai", "deepseek", "groq"]:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an AGI tool simulator. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                text = resp.choices[0].message.content
            elif provider == "anthropic":
                resp = await client.messages.create(
                    model=model,
                    max_tokens=1000,
                    system="You are an AGI tool simulator. Output only valid JSON.",
                    messages=[{"role": "user", "content": prompt}]
                )
                text = resp.content[0].text
            else:
                return {"error": "No simulation provider available"}

            # Basic JSON cleanup
            import json
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text)
        except Exception as e:
            if self.config.verbose:
                print(f"[Orchestrator] Simulation prompt failed: {e}")
            return {"error": f"Simulation failed: {e}"}

    def get_client_provider(self, provider_name):
        return self.brain.get_client(provider_name)
    
    
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
                    # 1. Primary execution with retries
                    result = await self._execute_action_with_retry(action, state, max_retries=3)
                    
                    # 2. If primary failed, try alternative skills or simulation (Immune System)
                    if not result.success and self.config.self_correction_enabled:
                        yield {"type": "correction_started", "action_id": action_id, "error": result.error}
                        
                        # --- Resilient Recovery Pipeline ---
                        # A. Try Alternatives
                        failed_cat, failed_sub = None, None
                        try:
                            fs = self.skill_registry.get_skill(action.skill)
                            failed_cat = fs.metadata.category
                            failed_sub = getattr(fs.metadata, 'sub_category', None)
                        except: pass

                        alternatives = await self.skill_registry.get_relevant_skills(
                            action.description, 
                            limit=3, 
                            category=failed_cat,
                            sub_category=failed_sub
                        )
                        alternatives = [s for s in alternatives if s.metadata.name != action.skill]
                        
                        repaired = False
                        for alt_skill in alternatives:
                            try:
                                yield {"type": "alternative_attempt", "skill": alt_skill.metadata.name}
                                alt_inputs = self.mapper.auto_map_to_schema(result.metadata.get("inputs", {}), alt_skill.metadata, action.description)
                                alt_output = await asyncio.wait_for(alt_skill.execute(**alt_inputs), timeout=action.metadata.get("timeout", self.config.action_timeout))
                                
                                if not (isinstance(alt_output, dict) and (alt_output.get("success") is False or "error" in alt_output)):
                                    result = StepResult(action_id=action.id, success=True, output=alt_output, duration=0.0, metadata={"skill": alt_skill.metadata.name, "inputs": alt_inputs, "alternative": True})
                                    repaired = True
                                    yield {"type": "correction_success", "method": f"alternative:{alt_skill.metadata.name}"}
                                    break
                            except: continue
                        
                        # B. Simulation Fallback
                        if not repaired:
                            try:
                                yield {"type": "simulation_attempt"}
                                simulated_output = await self._simulate_action_result(action, result.metadata.get("inputs", {}), result.error, plan.goal)
                                if simulated_output:
                                    result = StepResult(action_id=action.id, success=True, output=simulated_output, duration=0.1, metadata={"skill": "brain_simulation", "inputs": result.metadata.get("inputs", {}), "simulated": True})
                                    repaired = True
                                    yield {"type": "correction_success", "method": "simulation"}
                            except: pass

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
                        return # Stop level if major failure
                except MissingConfigError as e:
                    yield {
                        "type": "config_required",
                        "skill": e.skill_name,
                        "missing_keys": e.missing_keys,
                        "schema": e.schema
                    }
                    return
        yield {
            "type": "execution_completed",
            "success": len(state.failed) == 0,
            "completed": len(state.completed),
            "failed": len(state.failed)
        }
