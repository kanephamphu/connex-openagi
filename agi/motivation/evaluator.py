"""
Evaluator for the Motivation System.

Uses the GenAI Brain to assess the quality of execution and suggest improvements.
"""

import json
from typing import List, Dict, Any, Optional
from agi.brain import GenAIBrain, TaskType

class Evaluator:
    """
    Evaluates execution traces and provides feedback.
    """
    
    def __init__(self, brain: GenAIBrain):
        self.brain = brain
        
    async def evaluate_performance(self, goal: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate the quality of actions taken to achieve a goal.
        """
        if not actions:
            return {"score": 1.0, "feedback": "No actions taken.", "needs_improvement": False}
            

        prompt = f"""
        You are the 'Self-Evaluation' module of an AGI.
        Analyze the following execution trace.
        
        Goal: "{goal}"
        
        Actions Taken:
        {json.dumps(actions, indent=2)}
        
        Criteria & Scoring (0.0 to 1.0):
        1. Success: Did the actions achieve the goal?
        2. Efficiency: Were there unnecessary steps?
        3. Safety: Were the actions safe and robust?
        
        Response Format (JSON):
        {{
            "scores": {{
                "success": 0.0,
                "efficiency": 0.0,
                "safety": 0.0
            }},
            "overall_score": 0.0,
            "feedback": "Concise summary.",
            "needs_improvement": true/false,
            "analysis": {{
                "root_cause": "Why it failed or was inefficient (optional)",
                "improvement_type": "skill_acquisition" or "logic_refinement" or "none",
                "suggested_action": "Specific action to take."
            }}
        }}
        """
        
        try:
            # use general reasoning for evaluation
            provider, model = self.brain.select_model(TaskType.PLANNING)
            client = self.brain.get_client(provider)
            
            if provider in ["openai", "deepseek", "groq"]:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2, # Low temp for consistent evaluation
                    response_format={"type": "json_object"} if provider != "groq" else None # Groq doesn't always support json_object
                )
                content = response.choices[0].message.content
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                content = response.content[0].text
            else:
                return {"score": 0.5, "feedback": "Unsupported provider for evaluation", "needs_improvement": False}

            return self._parse_json(content)
            
        except Exception as e:
            print(f"[Evaluator] Evaluation failed: {e}")
            return {"score": 0.5, "feedback": f"Evaluation error: {e}", "needs_improvement": False}

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Utility to extract JSON from model response."""
        try:
            # find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return {"score": 0.5, "feedback": "Failed to parse evaluation response", "needs_improvement": False}
