"""
Utility functions for the AGI Dashboard.
"""

import asyncio
import functools
import json
from typing import Any, Dict

def async_handler(func):
    """Decorator to run async functions in Streamlit."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper

def format_thought_process(step: Dict[str, Any]) -> str:
    """Format a planning step for display."""
    if step["type"] == "planning_started":
        return f"**Planning Goal**: {step.get('goal')}"
    elif step["type"] == "reasoning_token":
        # Usually aggregated in UI, but individual tokens handled elsewhere
        return step.get("token", "")
    elif step["type"] == "plan_complete":
        plan = step.get("plan", {})
        if hasattr(plan, "actions"): # It's an ActionPlan object
             actions = plan.actions
             reasoning = plan.reasoning
        else:
             actions = plan.get("actions", [])
             reasoning = plan.get("reasoning", "")
             
        output = f"**Plan Generated** ({len(actions)} steps)\n\n"
        output += f"*Reasoning*: {reasoning}\n\n"
        for i, action in enumerate(actions, 1):
            act_dict = action.to_dict() if hasattr(action, "to_dict") else action
            output += f"{i}. **{act_dict.get('skill')}**: {act_dict.get('description')}\n"
        return output
    return str(step)

def format_execution_step(step: Dict[str, Any]) -> str:
    """Format an execution step for display."""
    if step["type"] == "step_started":
        return f"🔄 **Executing Step {step['step_id']}**: {step['action'].get('description')}"
    elif step["type"] == "tool_execution":
        return f"🛠️ **Tool Call ({step['skill']})**:\nInputs: `{json.dumps(step['inputs'])}`"
    elif step["type"] == "step_completed":
        result = step['result']
        output = result.get('output', {})
        # Truncate long outputs
        out_str = json.dumps(output, indent=2)
        if len(out_str) > 500:
            out_str = out_str[:500] + "... (truncated)"
        return f"✅ **Result**:\n```json\n{out_str}\n```"
    elif step["type"] == "error":
        return f"❌ **Error**: {step.get('error')}"
    return ""
