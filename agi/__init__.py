"""
Connex AGI - Three-tier Agentic Planning System

This package implements a sophisticated AGI architecture that transforms user interactions
into structured, executable action sequences.

Architecture:
    - Tier 1 (Planner): Decomposes goals into action DAGs using high-reasoning models
    - Tier 2 (Orchestrator): Manages state and routes actions to appropriate skills
    - Tier 3 (SkillDock): Registry of modular skills that perform actual work

Usage:
    >>> from agi import AGI
    >>> agi = AGI()
    >>> result = await agi.execute("Analyze my brand's competitors")
"""

from agi.config import AGIConfig
from agi.brain import GenAIBrain
from agi.planner import Planner
from agi.orchestrator import Orchestrator
from agi.skilldock import SkillRegistry
from agi.history import HistoryManager
from agi.perception import PerceptionLayer
from agi.reflex import ReflexLayer

__version__ = "0.1.1"
__all__ = ["AGI", "AGIConfig", "Planner", "Orchestrator", "SkillRegistry", "GenAIBrain"]


class AGI:
    """
    Main AGI interface that coordinates all three tiers.
    """
    
    def __init__(self, config: AGIConfig | None = None):
        """
        Initialize the AGI system.
        """
        self.config = config or AGIConfig.from_env()
        self.brain = GenAIBrain(self.config)
        
        from agi.planner.brain_planner import BrainPlanner
        self.planner = BrainPlanner(self.config)
        self.skill_registry = SkillRegistry(self.config)
        self.orchestrator = Orchestrator(
            config=self.config,
            skill_registry=self.skill_registry
        )
        # Tier Peer Layers
        self.perception = PerceptionLayer(self.config)
        self.reflex = ReflexLayer(self.config)
        
        self.history = HistoryManager(data_dir=str(self.config.data_dir) if hasattr(self.config, 'data_dir') else "data")

    async def initialize(self):
        """Perform async initialization tasks."""
        if self.config.verbose:
            print("[AGI] Running startup initialization...")
        await self.skill_registry.ensure_embeddings()
        await self.skill_registry.initialize_all_skills()
        if self.config.verbose:
            print("[AGI] Initialization complete.")
    
    async def execute(self, goal: str, context: dict | None = None) -> dict:
        """
        Execute a goal using the three-tier AGI system.
        
        Args:
            goal: Natural language description of what to accomplish
            context: Optional context information and constraints
            
        Returns:
            Dictionary containing results, execution trace, and metadata
            
        Example:
            >>> result = await agi.execute(
            ...     "Find and summarize my top 5 competitors",
            ...     context={"industry": "SaaS", "region": "US"}
            ... )
        """
        # Tier 1: Plan the actions
        plan = await self.planner.create_plan(goal, context or {})
        
        # Tier 2 & 3: Execute the plan
        result = await self.orchestrator.execute_plan(plan)
        
        return {
            "success": result.success,
            "result": result.output,
            "plan": plan.to_dict(),
            "execution_trace": result.trace,
            "metadata": {
                "steps_executed": len(result.trace),
                "errors": result.errors,
                "duration_seconds": result.duration,
            }
        }
    
    async def execute_with_streaming(self, goal: str, context: dict | None = None):
        """
        Execute a goal with real-time streaming of progress.
        """
        if self.config.verbose:
            print(f"[AGI] execute_with_streaming called for: {goal}")
        
        # Trace capture for history
        full_trace = []
        
        try:
            # Helper to yield and capture
            async def yield_and_capture(evt):
                full_trace.append(evt)
                yield evt

            async for evt in yield_and_capture({"phase": "planning", "type": "planning_started", "goal": "Analyzing your request..."}):
                yield evt
            
            # --- NEW: Reasoning Phase (Inner Monologue) ---
            if self.config.verbose:
                print("[AGI] Entering reasoning phase...")
            reasoning_content = ""
            
            # Inject available skills so the Brain knows what it can do
            skill_list = [s.name for s in self.skill_registry.list_skills()]
            reasoning_context = {**(context or {}), "available_skills": skill_list}
            
            async for update in self.brain.reason(goal, reasoning_context):
                if update["type"] == "reasoning_token":
                    reasoning_content += update["token"]
                # We don't capture every token in trace to save space, only final content or chunks?
                # Actually, UI needs tokens. But storing thousands of tokens in JSON is bad.
                # Let's verify if we want to store tokens. For now, yes, but maybe consolidated later.
                full_trace.append({"phase": "planning", **update, "partial_content": reasoning_content})
                yield {"phase": "planning", **update, "partial_content": reasoning_content}

            if self.config.verbose:
                print("[AGI] Reasoning complete. Classifying intent...")

            # --- Intent Classification ---
            intent = await self.brain.classify_intent(goal)
            if self.config.verbose:
                print(f"[AGI] Detected intent: {intent}")
                
            if intent == "CHAT":
                if self.config.verbose:
                    print("[AGI] Executing CHAT intent...")
                provider, model = self.brain.select_model("fast")
                client = self.brain.get_client(provider)
                
                # Streaming response generation
                stream = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": goal}],
                    temperature=0.7,
                    max_tokens=800,
                    stream=True
                )
                
                content = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        content += token
                        evt = {
                            "phase": "execution",
                            "type": "action_completed",
                            "action_id": "chat_response",
                            "output": {"reply": content}
                        }
                        # Only append the final complete event to trace, or streamed?
                        # For chat, we might want just the final answer in history.
                        # But loop needs to yield tokens.
                        yield evt
                
                # Append final result to trace
                full_trace.append({
                    "phase": "execution",
                    "type": "action_completed", 
                    "action_id": "chat_response", 
                    "output": {"reply": content}
                })
                return

            # Tier 1: Plan the actions (ACTION intent)
            if self.config.verbose:
                print("[AGI] Creating plan...")
            final_plan = None
            async for update in self.planner.create_plan_streaming(goal, context or {}):
                if update.get("type") == "planning_started":
                    continue # Already yielded initial planning start
                if "plan" in update and hasattr(update["plan"], "to_dict"):
                    final_plan = update["plan"]
                    update["plan"] = final_plan.to_dict()
                
                full_trace.append({"phase": "planning", **update})
                yield {"phase": "planning", **update}
            
            if not final_plan:
                if self.config.verbose:
                    print("[AGI] No plan generated.")
                return

            # Stream execution phase
            if self.config.verbose:
                print("[AGI] Executing plan...")
            async for update in self.orchestrator.execute_plan_streaming(final_plan):
                # StepResult objects might be in the update, handle them
                if "result" in update and hasattr(update["result"], "to_dict"):
                    update["result"] = update["result"].to_dict()
                
                full_trace.append({"phase": "execution", **update})
                yield {"phase": "execution", **update}

        except Exception as e:
            print(f"[AGI] CRITICAL ERROR in execute_with_streaming: {e}")
            import traceback
            traceback.print_exc()
            err_evt = {"phase": "planning", "type": "error", "message": str(e)}
            full_trace.append(err_evt)
            yield err_evt
            
        finally:
            # Save history
            try:
                self.history.add_trace(goal, full_trace)
            except Exception as h_err:
                print(f"[AGI] Failed to save history: {h_err}")
