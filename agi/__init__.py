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

import asyncio
from typing import Dict, Any, List, Optional
from agi.config import AGIConfig
from agi.brain import GenAIBrain
from agi.planner import Planner
from agi.orchestrator import Orchestrator
from agi.skilldock import SkillRegistry
from agi.history import HistoryManager
from agi.perception import PerceptionLayer
from agi.reflex import ReflexLayer
from agi.memory.manager import MemoryManager
from agi.motivation.engine import MotivationEngine
from agi.sub_brain import SubBrainManager

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
        self.sub_brain = SubBrainManager(self.config)
        self.loop = asyncio.get_event_loop() # Store loop for thread-safe sensor callbacks
        
        # Audio Management
        from agi.utils.audio_manager import audio_manager
        audio_manager.config = self.config
        audio_manager.set_loop(self.loop)
        
        from agi.planner.brain_planner import BrainPlanner
        self.planner = BrainPlanner(self.config)
        self.skill_registry = SkillRegistry(self.config)
        
        if getattr(self.config, 'enable_world_recognition', True):
            from agi.world.manager import WorldManager
            self.world = WorldManager(self.config, self.brain)
        else:
            self.world = None
        
        self.orchestrator = Orchestrator(
            config=self.config,
            skill_registry=self.skill_registry,
            world_manager=self.world
        )
        # Tier Peer Layers
        self.perception = PerceptionLayer(self.config)
        if self.world:
            self.perception.grounding_callback = self.world.handle_perception
        
        self.reflex = ReflexLayer(self.config)
        self.memory = MemoryManager(self.config, self.brain)
        setattr(self.config, 'memory_manager', self.memory)
        
        # Register new memory skill manually if not dynamic already
        from agi.skilldock.skills.memory.scripts.agent import MemorySkill
        self.skill_registry.register(MemorySkill(self.config))
        
        # Motivation System
        self.motivation = MotivationEngine(self.config, self.brain)
        from agi.skilldock.skills.skill_acquisition.scripts.agent import SkillAcquisitionSkill
        self.skill_registry.register(SkillAcquisitionSkill(self.config))
        
        # Output Skills
        from agi.skilldock.skills.speak.scripts.agent import SpeakSkill
        from agi.skilldock.skills.browser.scripts.agent import BrowserSkill
        from agi.skilldock.skills.system.scripts.agent import SystemControlSkill
        from agi.skilldock.skills.weather.scripts.agent import WeatherSkill
        
        self.skill_registry.register(SpeakSkill(self.config))
        self.skill_registry.register(BrowserSkill(self.config))
        self.skill_registry.register(SystemControlSkill(self.config))
        self.skill_registry.register(WeatherSkill(self.config))
        
        # Core Foundation Skills
        from agi.skilldock.skills.general_chat.scripts.agent import GeneralChatSkill
        from agi.skilldock.skills.text_analyzer.scripts.agent import TextAnalyzerSkill
        from agi.skilldock.skills.web_search.scripts.agent import WebSearchSkill
        from agi.skilldock.skills.file_manager.scripts.agent import FileManagerSkill
        
        self.skill_registry.register(GeneralChatSkill(self.config))
        self.skill_registry.register(TextAnalyzerSkill(self.config))
        self.skill_registry.register(WebSearchSkill(self.config))
        self.skill_registry.register(FileManagerSkill(self.config))
        
        # Internal Interface Skill
        from agi.skilldock.skills.agi_interface.scripts.agent import AGIInterfaceSkill
        self.skill_registry.register(AGIInterfaceSkill(self.config, self.execute))
        
        # Emotion Skill
        from agi.skilldock.skills.emotion.scripts.agent import EmotionDetectionSkill
        self.skill_registry.register(EmotionDetectionSkill(self.config))
        
        self.history = HistoryManager(data_dir=str(self.config.data_dir) if hasattr(self.config, 'data_dir') else "data")
        
        # Set default verbose for demo if not in environment
        if not hasattr(self.config, 'verbose_explicit'): # Check if user explicitly set it
             self.config.verbose = True

    async def initialize(self):
        """Perform async initialization tasks."""
        if self.config.verbose:
            print("[AGI] Running startup initialization...")
        await self.sub_brain.initialize()
        from agi.identity.manager import IdentityManager
        self.identity = IdentityManager(self.config)
        
        await self.skill_registry.ensure_embeddings()
        await self.skill_registry.initialize_all_skills()
        # Attach sub-brain to config for easier perception access
        if getattr(self.config, 'enable_world_recognition', True):
            from agi.world.manager import WorldManager
            self.world = WorldManager(self.config, self.brain)
        else:
            self.world = None

        setattr(self.config, 'sub_brain_manager', self.sub_brain)
        
        await self.perception.initialize(
            memory_manager=self.memory, 
            skill_registry=self.skill_registry,
            identity_manager=self.identity
        )
        # Wire Perception to Planner for context awareness
        if hasattr(self.planner, 'set_perception_layer'):
            self.planner.set_perception_layer(self.perception)
            
        await self.reflex.initialize(history_manager=self.history)

        # Initialize and Start the 'Ear' sensor
        try:
            from agi.sensors.ear.ear_sensor import VoiceEar
            self.ear = VoiceEar(self.config, on_event_callback=self.handle_sensor_event_sync)
            self.ear.start()
        except Exception as e:
            if self.config.verbose:
                print(f"[AGI] Could not start Ear sensor: {e}")

        # Initialize and Start the 'Time' sensor
        try:
            from agi.sensors.time.time_sensor import TimeSensor
            self.time_sensor = TimeSensor(self.config, on_event_callback=self.handle_sensor_event_sync)
            self.time_sensor.start()
        except Exception as e:
            if self.config.verbose:
                print(f"[AGI] Could not start Time sensor: {e}")

        if self.config.verbose:
            print("[AGI] Initialization complete.")

    def handle_sensor_event_sync(self, event: Dict[str, Any]):
        """Thread-safe gateway for sensors to inject events into the AGI."""
        if hasattr(self, 'loop') and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.handle_reflex_event(event), self.loop)
        else:
            # Fallback if loop is not yet running (startup)
            pass

    async def handle_reflex_event(self, event: Dict[str, Any]):
        """
        Process a reflex event (from Ear, Webhook, etc.)
        """
        if self.config.verbose:
            print(f"[AGI] Handling reflex event: {event.get('type')}")
        
        triggered_plans = await self.reflex.process_event(event)
        
        for tp in triggered_plans:
            reflex_name = tp["reflex"]
            plan = tp["plan"]
            
            if self.config.verbose:
                print(f"[AGI] Executing reflex plan for '{reflex_name}'")
            
            # Execute the plan via orchestrator
            # We add a callback to catch exceptions in the task
            def task_done_callback(t):
                try:
                    t.result()
                except Exception as e:
                    print(f"[AGI] Exception in reflex task '{reflex_name}': {e}")
                    import traceback
                    traceback.print_exc()

            task = asyncio.create_task(self.orchestrator.execute_plan(plan))
            task.add_done_callback(task_done_callback)

    async def execute(self, goal: str, context: dict | None = None, speak_output: bool = False) -> dict:
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
        if self.config.verbose:
            print(f"[AGI] Decomposing goal: '{goal}'")
            if context:
                print(f"[AGI] Context: {context}")

        # --- Emotion Detection (Parallel via Sub-Brains) ---
        asyncio.create_task(self.perception.perceive("emotion", goal))

        # --- NEW: Working Memory Integration ---
        working_memory = self.memory.get_working_memory()
        emotional_context = self.memory.emotional_state
        
        # Fetch Notable Info
        from agi.utils.database import DatabaseManager
        db = DatabaseManager()
        notable_info = db.get_all_notable_info()

        merged_context = {
            **(context or {}),
            "conversation_history": working_memory["recent_history"],
            "conversation_summary": working_memory["summary"],
            "notable_information": notable_info, 
            **emotional_context
        }

        # --- Intent Routing ---
        intent = await self.brain.classify_intent_fast(goal, working_memory, self.sub_brain)
        if self.config.verbose:
            print(f"[AGI] Detected intent: {intent}")
            
        if intent == "CHAT":
            if self.config.verbose:
                print("[AGI] Handling goal as direct CHAT.")
            chat_skill = self.skill_registry.get_skill("general_chat")
            # Pass history to chat skill for better turn-aware replies
            chat_result = await chat_skill.execute(message=goal, history=working_memory["recent_history"])
            reply = chat_result.get("reply", "")
            
            if speak_output and reply:
                speak_skill = self.skill_registry.get_skill("speak")
                await speak_skill.execute(text=reply)

            # Store in memory
            self.memory.add_to_short_term(goal, reply)
            asyncio.create_task(self.memory.update_conversation_summary())

            return {
                "success": True,
                "result": reply,
                "plan": {"goal": goal, "actions": []},
                "execution_trace": [],
                "metadata": {"intent": "CHAT"}
            }

        # Tier 1: Plan the actions (RESEARCH, SINGLE_ACTION, or PLAN intent)
        # Get relevant, enabled skills
        skills = await self.skill_registry.get_relevant_skills(goal)
        plan = await self.planner.create_plan(goal, merged_context, skills)
        
        if self.config.verbose:
            print(f"[AGI] Plan created with {len(plan.actions)} actions.")
            for i, action in enumerate(plan.actions):
                print(f"  {i+1}. {action.id} ({action.skill}): {action.description}")

        # Tier 2 & 3: Execute the plan
        result = await self.orchestrator.execute_plan(plan)
        
        if self.config.verbose:
            print(f"[AGI] Execution completed. Success: {result.success}")

        # Finalize response
        final_reply = ""
        # If we need to speak the final result
        if speak_output:
            if result.success:
                final_reply = str(result.output.get("reply") or result.output.get("text") or result.output.get("response") or "Task completed.")
            else:
                error_list = result.errors or ["An unknown error occurred."]
                final_reply = f"I'm sorry, I encountered an error: {error_list[0]}"
            
            if final_reply:
                speak_skill = self.skill_registry.get_skill("speak")
                await speak_skill.execute(text=final_reply)

        # Store in memory
        self.memory.add_to_short_term(goal, final_reply or str(result.output))
        asyncio.create_task(self.memory.update_conversation_summary())
        
        
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
            async def yield_evt(evt: Dict[str, Any]):
                """Helper to log and yield events."""
                full_trace.append(evt)
                yield evt

            async for evt in yield_evt({"phase": "planning", "type": "planning_started", "goal": "Analyzing your request..."}):
                yield evt
            
            # --- NEW: Reasoning Phase (Inner Monologue) ---
            if self.config.verbose:
                print("[AGI] Entering reasoning phase...")
            
            # --- Emotion Detection (Parallel via Sub-Brains) ---
            asyncio.create_task(self.perception.perceive("emotion", goal))
            
            reasoning_content = ""
            
            # Inject available skills so the Brain knows what it can do
            skill_list = [s.name for s in self.skill_registry.list_skills()]
            reasoning_context = {**(context or {}), "available_skills": skill_list}
            
            async for update in self.brain.reason(goal, reasoning_context):
                if update["type"] == "reasoning_token":
                    reasoning_content += update["token"]
                
                # Capture reasoning updates
                async for evt in yield_evt({"phase": "planning", **update, "partial_content": reasoning_content}):
                    yield evt

            if self.config.verbose:
                print("[AGI] Reasoning complete. Classifying intent...")

            # --- NEW: Working Memory ---
            working_memory = self.memory.get_working_memory()
            emotional_context = self.memory.emotional_state
            
            # Fetch Notable Info
            from agi.utils.database import DatabaseManager
            db = DatabaseManager()
            notable_info = db.get_all_notable_info()
            
            merged_context = {
                **(context or {}),
                "conversation_history": working_memory["recent_history"],
                "conversation_summary": working_memory["summary"],
                "notable_information": notable_info,
                **emotional_context
            }

            # --- Intent Classification ---
            intent = await self.brain.classify_intent_fast(goal, working_memory, self.sub_brain)
            if self.config.verbose:
                print(f"[AGI] Detected intent: {intent}")
                
            if intent == "CHAT":
                if self.config.verbose:
                    print("[AGI] Executing CHAT intent...")
                provider, model = self.brain.select_model("fast")
                client = self.brain.get_client(provider)
                
                # Direct Chat with history
                chat_messages = []
                if working_memory["summary"]:
                    chat_messages.append({"role": "system", "content": f"Conversation Summary: {working_memory['summary']}"})
                
                for msg in working_memory["recent_history"]:
                    chat_messages.append(msg)
                
                chat_messages.append({"role": "user", "content": goal})

                # Streaming response generation
                stream = await client.chat.completions.create(
                    model=model,
                    messages=chat_messages,
                    temperature=0.7,
                    max_tokens=800,
                    stream=True
                )
                
                content = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        content += token
                        async for evt in yield_evt({
                            "phase": "execution",
                            "type": "action_completed",
                            "action_id": "chat_response",
                            "output": {"reply": content}
                        }):
                            yield evt
                
                # Store final in memory
                self.memory.add_to_short_term(goal, content)
                asyncio.create_task(self.memory.update_conversation_summary())
                return

            # Tier 1: Plan the actions (RESEARCH, SINGLE_ACTION, or PLAN intent)
            if self.config.verbose:
                print("[AGI] Creating plan...")
            
            # Get relevant, enabled skills
            skills = await self.skill_registry.get_relevant_skills(goal)
            
            final_plan = None
            async for update in self.planner.create_plan_streaming(goal, merged_context, skills):
                if update.get("type") == "planning_started":
                    continue # Already yielded initial planning start
                if "plan" in update and hasattr(update["plan"], "to_dict"):
                    final_plan = update["plan"]
                    update["plan"] = final_plan.to_dict()
                
                async for evt in yield_evt({"phase": "planning", **update}):
                    yield evt
            
            if not final_plan:
                if self.config.verbose:
                    print("[AGI] No plan generated.")
                return

            # Stream execution phase
            if self.config.verbose:
                print("[AGI] Executing plan...")
            async for update in self.orchestrator.execute_plan_streaming(final_plan):
                if "result" in update and hasattr(update["result"], "to_dict"):
                    update["result"] = update["result"].to_dict()
                
                async for evt in yield_evt({"phase": "execution", **update}):
                    yield evt

            # --- NEW: Persistence Stage ---
            if final_plan:
                self.memory.add_to_short_term(goal, "Task completed successfully.") 

            # --- NEW: Motivation Stage ---
            if self.config.verbose:
                print("[AGI] Entering Motivation phase...")
            
            improvement_suggestion = await self.motivation.review_performance(goal)
            if improvement_suggestion:
                improvement_plan_action = await self.motivation.generate_improvement_plan(improvement_suggestion)
                if improvement_plan_action:
                    # Create a mini-plan for improvement
                    from agi.planner.base import ActionPlan, ActionNode
                    
                    imp_action = ActionNode(
                        id=improvement_plan_action["id"],
                        skill=improvement_plan_action["skill"],
                        description=improvement_plan_action["description"],
                        inputs=improvement_plan_action["inputs"],
                        depends_on=[]
                    )
                    improvement_dag = ActionPlan(goal=goal, actions=[imp_action])
                    
                    async for evt in yield_evt({"phase": "motivation", "type": "improvement_triggered", "suggestion": improvement_suggestion}):
                        yield evt
                    
                    async for update in self.orchestrator.execute_plan_streaming(improvement_dag):
                        if "result" in update and hasattr(update["result"], "to_dict"):
                            update["result"] = update["result"].to_dict()
                        async for evt in yield_evt({"phase": "motivation", **update}):
                            yield evt

        except Exception as e:
            error_msg = str(e)
            print(f"[AGI] CRITICAL ERROR in execute_with_streaming: {error_msg}")
            import traceback
            traceback.print_exc()
            
            err_evt = {"phase": "planning", "type": "error", "message": error_msg}
            full_trace.append(err_evt)
            yield err_evt
            
            # Announce error if speaking is enabled
            if self.config.is_speaking or getattr(self.config, 'speak_output', False):
                try:
                    speak_skill = self.skill_registry.get_skill("speak")
                    if speak_skill:
                        await speak_skill.execute(text=f"I'm sorry, I encountered an error: {error_msg}")
                except:
                    pass
        # finally:
            # # Save history
            # try:
            #     self.history.add_trace(goal, full_trace)
            # except Exception as h_err:
            #     if self.config.verbose:
            #         print(f"[AGI] Failed to save history: {h_err}")
            
    async def _handle_fast_intent(self, intent: str, goal: str, speak_output: bool) -> Optional[Dict[str, Any]]:
        """
        Handle simple intents using direct skill execution to save resources.
        """
        if intent == "RESEARCH":
            skill_selector_prompt = (
                "Select the best skill and extract parameters for this research goal.\n"
                "- If asking about weather: skill='weather', params={'location': 'City'}\n"
                "- Otherwise: skill='web_search', params={'query': 'Search query'}\n"
            )
        elif intent == "SINGLE_ACTION":
            skill_selector_prompt = (
                "Select the best skill and extract parameters for this single action.\n"
                "- System control: skill='system_control', VALID ACTIONS: [open_app, close_app, set_volume, set_brightness, screenshot, lock, sleep, toggle_dark_mode, notification, open_url]. params={'action': '...', 'app_name': '...', 'level': 0-100, 'url': '...'}\n"
                "- File management: skill='file_manager', VALID ACTIONS: [read_file, write_file, list_directory, delete_file, move_file, search_files, get_file_info]. params={'action': '...', 'path': '...', 'content': '...'}\n"
            )
        else:
            return None

        if self.config.verbose:
            print(f"[AGI] Fast-tracking {intent}...")

        # 1. Parameter Extraction & Skill Selection via Sub-Brain
        try:
            task = {
                "prompt": f"Goal: \"{goal}\"\n{skill_selector_prompt}\nRespond with ONLY valid JSON: {{\"skill\": \"name\", \"params\": {{...}}}}",
                "system": "You are a task routing specialist. Output only valid JSON."
            }
            extraction_results = await self.sub_brain.execute_parallel([task])
            result_raw = extraction_results[0] if extraction_results else "{}"
            
            # Basic JSON cleanup
            if "```" in result_raw:
                result_raw = result_raw.split("```")[1].strip()
                if result_raw.startswith("json"):
                    result_raw = result_raw[4:].strip()
            
            import json
            decision = json.loads(result_raw)
            skill_name = decision.get("skill")
            params = decision.get("params", {})
            
            if not skill_name:
                return None
                
        except Exception as e:
            if self.config.verbose:
                print(f"[AGI] Fast routing failed: {e}. Falling back to Planner.")
            return None

        # 2. Execute Skill Directly
        try:
            skill = self.skill_registry.get_skill(skill_name)
            if not skill:
                if self.config.verbose:
                    print(f"[AGI] Fast-track skill '{skill_name}' not found.")
                return None
                
            result_data = await skill.execute(**params)
            
            # 3. Handle Speak and Memory
            reply = ""
            is_error = "error" in result_data or result_data.get("success") is False
            
            if is_error:
                error_msg = result_data.get("error") or result_data.get("message") or "Unknown error."
                reply = f"I'm sorry, I encountered an error: {error_msg}"
            elif skill_name == "weather":
                reply = f"The weather in {result_data.get('location')} is {result_data.get('temperature')}°C and {result_data.get('condition')}."
            elif skill_name == "web_search":
                reply = f"I found some information about that: {str(result_data.get('results', []))[:200]}..."
            elif result_data.get("message"):
                reply = result_data["message"]
            else:
                reply = f"I've executed {skill_name} for you."

            if speak_output and reply:
                speak_skill = self.skill_registry.get_skill("speak")
                if speak_skill:
                    await speak_skill.execute(text=reply)

            self.memory.add_to_short_term(goal, reply)
            asyncio.create_task(self.memory.update_conversation_summary())

            return {
                "success": result_data.get("success", True),
                "result": result_data,
                "plan": {"goal": goal, "fast_intent": intent, "selected_skill": skill_name},
                "execution_trace": [{"skill": skill_name, "params": params, "result": result_data}],
                "metadata": {"intent": intent, "fast_path": True}
            }
        except Exception as e:
            if self.config.verbose:
                print(f"[AGI] Fast execution failed: {e}. Falling back to Planner.")
            return None
