"""
Brain-driven Planner implementation.

Uses the GenAI Brain's model selection to perform action decomposition, supporting any configured provider (OpenAI, DeepSeek, Anthropic, etc.).
"""

import json
import time
from typing import Dict, Any

# Note: System prompt is now generated dynamically per request via render_system_prompt in schemas.py
from agi.planner.schemas import render_system_prompt


class BrainPlanner(Planner):
    """
    Generic Planner implementation using the Brain's selected high-reasoning model.
    """
    
    
    def __init__(self, config):
        super().__init__(config)
        self.perception_layer = None
        
    def set_perception_layer(self, layer):
        self.perception_layer = layer
        
    async def _gather_relevant_context(self, goal: str) -> Dict[str, Any]:
        """
        Ask the Brain which perceptions are relevant (by description), then fetch them.
        Query logic: LLM -> keywords -> DB Query -> Modules -> Fetch.
        """
        if not self.perception_layer:
            return {}
            
        # 1. Ask Brain for generic needs (Semantic Phrase)
        prompt = (
            f"Goal: {goal}\n"
            f"Identify what kind of environmental information is needed to achieve this goal.\n"
            f"Return a JSON object with a key 'search_phrase' containing a short natural language phrase describing the needed context (e.g. 'local weather conditions'). Return empty string if none."
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.planner_model,
                messages=[
                    {"role": "system", "content": "You are a context-aware system. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            selection = json.loads(response.choices[0].message.content)
            phrase = selection.get("search_phrase", "")
            
            if not phrase:
                return {}
                
            # 2. Semantic Search via Perception Layer
            candidates = set()
            if hasattr(self.perception_layer, 'search_sensors'):
                 matches = await self.perception_layer.search_sensors(phrase)
                 candidates.update(matches)
            
            # 3. Fetch data for candidates
            context_data = {}
            for name in candidates:
                try:
                    data = await self.perception_layer.perceive(name)
                    context_data[name] = data
                except:
                    pass
                    
            return context_data
            
        except Exception as e:
            if self.config.verbose:
                print(f"[BrainPlanner] Context selection failed: {e}")
            return {}
            
        except Exception as e:
            if self.config.verbose:
                print(f"[BrainPlanner] Context selection failed: {e}")
            return {}

    async def create_plan(self, goal: str, context: dict, skills: List[Any]) -> ActionPlan:
        """
        Create an action plan using the configured planner model.
        """
        start_time = time.time()
        
        # 0. Generate Dynamic System Prompt
        system_prompt = render_system_prompt(skills)
        
        # Smart Context Retrieval
        sensor_context = await self._gather_relevant_context(goal)
        if sensor_context:
            context = {**context, "sensor_data": sensor_context}
        
        # Build prompt
        user_prompt = build_planning_prompt(goal, context)
        
        if self.config.verbose:
            print(f"\n[BrainPlanner] Planning for goal: {goal}")
            print(f"[BrainPlanner] Using model: {self.config.planner_model}")
        
        # Call API with structured output
        try:
            # We need to handle different client types slightly differently if needed
            # But mostly they follow OpenAI format if using OpenAI/DeepSeek/Groq
            # Anthropic handles json mode differently.
            
            # For robust compatibility, we assume the client is wrapped or compatible.
            # config.get_planner_client() returns AsyncOpenAI or AsyncAnthropic.
            
            if "anthropic" in str(type(self.client)).lower():
                 response = await self.client.messages.create(
                    model=self.config.planner_model,
                    system=PLANNER_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_prompt + "\nRespond with valid JSON only."}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                 content = response.content[0].text
                 
            else:
                # OpenAI / DeepSeek / Groq
                response = await self.client.chat.completions.create(
                    model=self.config.planner_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
            
            # Parse response
            plan_data = json.loads(content)
            
            # Validate against schema
            validated_plan = ActionPlanSchema.model_validate(plan_data)
            
            # Convert to ActionPlan
            actions = []
            for action_schema in validated_plan.actions:
                # Merge static inputs and references
                all_inputs = {**action_schema.inputs}
                
                action = ActionNode(
                    id=action_schema.id,
                    skill=action_schema.skill,
                    description=action_schema.description,
                    inputs=all_inputs,
                    input_schema=action_schema.input_refs,
                    output_schema=action_schema.output_schema,
                    depends_on=action_schema.depends_on,
                    priority=action_schema.priority,
                )
                actions.append(action)
            
            plan = ActionPlan(
                goal=goal,
                actions=actions,
                reasoning=validated_plan.reasoning,
                metadata={
                    "planner": "brain_planner",
                    "model": self.config.planner_model,
                    "context": context,
                }
            )
            
            # planning_time = time.time() - start_time
            
            if self.config.verbose:
                print(f"[BrainPlanner] Created plan with {len(actions)} actions")
            
            return plan
            
        except Exception as e:
            if self.config.verbose:
                print(f"[BrainPlanner] Error: {e}")
            raise ValueError(f"Planning failed: {e}")
    
    async def create_plan_streaming(self, goal: str, context: dict, skills: List[Any]):
        """
        Create plan with streaming of reasoning process.
        """
        yield {"type": "planning_started", "goal": goal}
        
        # 0. Generate Dynamic System Prompt
        system_prompt = render_system_prompt(skills)
        
        # Smart Context Retrieval
        sensor_context = await self._gather_relevant_context(goal)
        if sensor_context:
            context = {**context, "sensor_data": sensor_context}
            yield {"type": "context_gathered", "data": sensor_context}
        
        # Build prompt
        user_prompt = build_planning_prompt(goal, context)
        
        # Stream the response
        try:
            content = ""
            
            if "anthropic" in str(type(self.client)).lower():
                 async with self.client.messages.stream(
                    model=self.config.planner_model,
                    system=PLANNER_SYSTEM_PROMPT,
                    max_tokens=self.config.max_tokens,
                    messages=[{"role": "user", "content": user_prompt + "\nRespond with valid JSON only."}],
                ) as stream:
                    async for text in stream.text_stream:
                        yield {
                            "type": "reasoning_token",
                            "token": text,
                            "partial_content": content + text
                        }
                        content += text
            else:
                stream = await self.client.chat.completions.create(
                    model=self.config.planner_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    response_format={"type": "json_object"},
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        content += token
                        yield {
                            "type": "reasoning_token",
                            "token": token,
                            "partial_content": content
                        }
            
            # Parse final plan
            try:
                plan_data = json.loads(content)
                validated_plan = ActionPlanSchema.model_validate(plan_data)
                
                # Convert to ActionPlan
                actions = []
                for action_schema in validated_plan.actions:
                    all_inputs = {**action_schema.inputs}
                    action = ActionNode(
                        id=action_schema.id,
                        skill=action_schema.skill,
                        description=action_schema.description,
                        inputs=all_inputs,
                        input_schema=action_schema.input_refs,
                        output_schema=action_schema.output_schema,
                        depends_on=action_schema.depends_on,
                        priority=action_schema.priority,
                    )
                    actions.append(action)
                
                plan = ActionPlan(
                    goal=goal,
                    actions=actions,
                    reasoning=validated_plan.reasoning,
                    metadata={
                        "planner": "brain_planner",
                        "model": self.config.planner_model,
                    }
                )
                
                yield {
                    "type": "plan_complete",
                    "plan": plan
                }
            except Exception as parse_err:
                 yield {
                    "type": "planning_error",
                    "error": f"Failed to parse plan JSON: {parse_err}"
                }
            
        except Exception as e:
            yield {
                "type": "planning_error",
                "error": str(e)
            }
