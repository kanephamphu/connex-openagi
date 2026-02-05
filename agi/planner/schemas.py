"""
Pydantic schemas for structured planner output.

Defines the JSON schemas that the LLM must follow when generating plans.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ActionNodeSchema(BaseModel):
    """Schema for a single action in the plan."""
    
    id: str = Field(description="Unique action ID (e.g., 'action_1')")
    skill: str = Field(description="Skill to invoke (e.g., 'web_search', 'code_executor')")
    description: str = Field(description="What this action accomplishes")
    
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Static input values"
    )
    input_refs: Dict[str, str] = Field(
        default_factory=dict,
        description="References to outputs from other actions (e.g., {'query': 'action_1.results'})"
    )
    
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected output structure (e.g., {'competitors': 'List[dict]' or JSON Schema})"
    )
    
    depends_on: List[str] = Field(
        default_factory=list,
        description="Action IDs that must complete first"
    )

    priority: str = Field(
        default="MAJOR",
        enum=["MAJOR", "MINOR", "SKIPPABLE"],
        description="Step priority (MAJOR, MINOR, SKIPPABLE). MAJOR: Critical. MINOR: Helpful. SKIPPABLE: Optional/Auxiliary, skip on any issue or for cost-saving."
    )


class ActionPlanSchema(BaseModel):
    """
    Schema for the complete action plan.
    
    This is what we ask the LLM to generate.
    """
    
    reasoning: str = Field(
        description="Step-by-step reasoning for how you decomposed this goal"
    )
    
    actions: List[ActionNodeSchema] = Field(
        description="Ordered list of actions to accomplish the goal"
    )
    
    expected_outcome: str = Field(
        default="",
        description="What the final result should look like"
    )

# System prompt for planning
PLANNER_SYSTEM_PROMPT_TEMPLATE = """You are an expert AI planner that decomposes complex goals into executable action sequences.

Your task is to create a DETAILED, STEP-BY-STEP plan that breaks down the user's goal into discrete actions.

# Available Skills

You must ONLY use the following skills. Do not invent new ones.

{skills_section}

# Planning Guidelines

1. **COST OPTIMIZATION - FEWEST STEPS**: You are a cost-focused planner. Create the **leanest possible plan** to achieve the goal. Minimize the number of skill calls. If one task can be inferred or combined into another, do it. Avoid redundant information gathering.
2. **Decompose Thoroughly**: Break complex tasks into small, focused actions, but only as many as strictly necessary.
3. **Define Dependencies**: Use `depends_on` to ensure proper ordering.
4. **Step Priority (Strictly assign one)**:
   - `MAJOR`: Critical core logic. Failure = Goal Failure.
   - `MINOR`: Enhancements. Failure = Warning, but continue.
   - `SKIPPABLE`: Non-essential/Auxiliary steps (e.g., logging, extra confirmation). These can be ignored if they add unnecessary cost or fail.
5. **Specify I/O**: Clearly define what each action produces and consumes.
6. **Use References**: Connect actions using `input_refs`.
7. **Direct Outcome**: Prefer direct actions over multi-step verification if the risk is low.
8. **Strict Parameters**: You MUST use the exact input parameter names listed in the skill definition. Do not invent keys like 'key' or 'action' if they are not in the schema.
9. **Skill Repair**: If `skill_file_path` is provided in context (due to an error), you represent the IMMUNE SYSTEM. You MUST:
   a. Use `file_manager` to READ the file.
   b. Identify the bug in your internal monologue.
   c. Use `file_manager` to WRITE the corrected code back to the file.
   d. Do NOT use 'problem_analyzer' or other hallucinated skills. Use ONLY `file_manager`.

# Output Format

You MUST respond with a valid JSON object matching the ActionPlanSchema:
{{
  "reasoning": "Step-by-step explanation...",
  "actions": [
    {{
      "id": "action_1",
      "skill": "web_search",
      "description": "Find info",
      "inputs": {{"query": "Search query"}},
      "output_schema": {{"results": "List[dict]"}},
      "depends_on": []
    }}
  ],
  "expected_outcome": "Description of result..."
}}
"""

# Alias for backward compatibility
PLANNER_SYSTEM_PROMPT = PLANNER_SYSTEM_PROMPT_TEMPLATE


def render_system_prompt(skills: List[Any]) -> str:
    """
    Render the system prompt with the given list of skills.
    
    Args:
        skills: List of Skill or SkillMetadata objects
        
    Returns:
        Formatted system prompt path
    """
    skills_text = ""
    for skill in skills:
        # Handle both Skill objects and SkillMetadata objects
        meta = skill.metadata if hasattr(skill, "metadata") else skill
        
        skills_text += f"- **{meta.name}**: {meta.description}\n"
        
        # Inputs
        inputs = []
        if meta.input_schema and "properties" in meta.input_schema:
            for name, prop in meta.input_schema["properties"].items():
                if isinstance(prop, dict):
                    desc = prop.get("description", "")
                    type_ = prop.get("type", "any")
                    enum_values = prop.get("enum", [])
                else:
                    desc = ""
                    type_ = str(prop)
                    enum_values = []
                
                if enum_values:
                    type_ = f"{type_} (Allowed: {', '.join(map(str, enum_values))})"
                
                inputs.append(f"{name} ({type_})")
        
        if not inputs:
            inputs.append("None")
            
        inputs_str = ", ".join(inputs)
        skills_text += f"  - Inputs: {inputs_str}\n"
        
        # Outputs
        outputs = []
        if meta.output_schema:
            # Handle both simple {key: type} and full JSON Schema
            if "properties" in meta.output_schema:
                for name, prop in meta.output_schema["properties"].items():
                    if isinstance(prop, dict):
                        type_ = prop.get("type", "any")
                    else:
                        type_ = str(prop)
                    outputs.append(f"{name} ({type_})")
            elif "type" in meta.output_schema and len(meta.output_schema) <= 2:
                # Likely just a type definition for the whole output
                outputs.append(f"Result ({meta.output_schema['type']})")
            else:
                # Simple mapping
                for name, type_ in meta.output_schema.items():
                    outputs.append(f"{name} ({type_})")
        
        if not outputs:
            outputs.append("None")
            
        outputs_str = ", ".join(outputs)
        skills_text += f"  - Outputs: {outputs_str}\n\n"
        
    return PLANNER_SYSTEM_PROMPT_TEMPLATE.format(skills_section=skills_text)


def build_planning_prompt(goal: str, context: dict) -> str:
    """
    Build the user prompt for the planner.
    
    Args:
        goal: User's goal
        context: Additional context
        
    Returns:
        Formatted prompt
    """
    prompt = f"# Goal\n\n{goal}\n\n"
    
    if context:
        prompt += "# Context\n\n"
        for key, value in context.items():
            prompt += f"- {key}: {value}\n"
        prompt += "\n"
    
    prompt += "Create a detailed action plan to accomplish this goal. "
    prompt += "Think step-by-step and output valid JSON matching the ActionPlanSchema."
    
    return prompt
