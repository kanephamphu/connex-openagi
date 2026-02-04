"""
Brain-driven Planner implementation.

Uses the GenAI Brain's model selection to perform action decomposition, supporting any configured provider (OpenAI, DeepSeek, Anthropic, etc.).
"""

import json
import time
from typing import Dict

from agi.planner.base import Planner, ActionPlan, ActionNode, PlannerResult
from agi.planner.schemas import (
    ActionPlanSchema,
    PLANNER_SYSTEM_PROMPT_TEMPLATE,
    build_planning_prompt
)

# Default to empty skills if not provided
PLANNER_SYSTEM_PROMPT = PLANNER_SYSTEM_PROMPT_TEMPLATE.format(skills_section="No specific skills provided.")


class BrainPlanner(Planner):
    """
    Generic Planner implementation using the Brain's selected high-reasoning model.
    """
    
    def __init__(self, config):
        super().__init__(config)
        # We don't bind a specific client here, we get it dynamically or use the one from base which uses config defaults.
        # Ideally, we should ask the Brain, but Planner is initialized with Config.
        # For now, base class Planner.__init__ calls config.get_planner_client(), which respects AGI_DEFAULT_PLANNER.
        # So self.client is already the correct client.
        
    async def create_plan(self, goal: str, context: dict) -> ActionPlan:
        """
        Create an action plan using the configured planner model.
        """
        start_time = time.time()
        
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
                        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
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
    
    async def create_plan_streaming(self, goal: str, context: dict):
        """
        Create plan with streaming of reasoning process.
        """
        yield {"type": "planning_started", "goal": goal}
        
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
                        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
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
