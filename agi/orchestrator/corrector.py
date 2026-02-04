"""
Self-Correction Module (The Immune System).

Analyzes tool failures and proactively fixes inputs to retry actions
without requiring a full replan.
"""

import json
from typing import Any, Dict, Optional
from agi.brain import GenAIBrain, TaskType

class Corrector:
    """
    The Immune System for the AGI.
    
    When an action fails, the Corrector analyzes the error and the inputs,
    and attempts to generate "patched" inputs that resolve the issue.
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
        
    async def correct(
        self, 
        skill_name: str, 
        original_inputs: Dict[str, Any], 
        error_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to fix a failed action.
        
        Args:
            skill_name: Name of the skill that failed
            original_inputs: The inputs that caused the failure
            error_message: The error returned by the skill
            
        Returns:
            Dict of fixed inputs, or None if correction failed/gave up.
        """
        # Construct the diagnostic prompt
        prompt = f"""
        ACUTION: A tool execution failed. Your task is to fix the inputs.
        
        Skill: {skill_name}
        
        Original Inputs:
        {json.dumps(original_inputs, indent=2)}
        
        Error Output:
        {error_message}
        
        INSTRUCTIONS:
        1. Analyze WHY the error occurred (e.g., SyntaxError in code, Invalid Argument, File missing).
        2. Propose NEW inputs that fix the specific error.
        3. Do NOT change the intent of the action. Only fix the implementation details.
        
        RESPONSE FORMAT:
        You must return ONLY a valid JSON object containing the fixed inputs.
        Example: {{"code": "print('fixed')"}}
        """
        
        try:
            # Use CODING capability if it's a code error, otherwise GENERAL reasoning
            # If skill is code_executor, favor coding model
            task_type = TaskType.CODING if skill_name == "code_executor" else TaskType.FAST
            
            # Use Brain to analyze
            # We don't have a structured "generate_json" method on Brain yet everywhere,
            # but select_model returns a client. We can just use a simple chat completion wrapper
            # provided by the brain or just use raw client.
            # brain.py doesn't have a "generate_response" method exposed directly?
            # Let's check imports. Env has GenAIBrain.
            
            # We will use select_model to get the best client for the job
            client_type, model_name = self.brain.select_model(task_type)
            client = self.brain.get_client(client_type)
            
            # Simple inference wrapper
            if client_type == "openai" or client_type == "deepseek" or client_type == "groq":
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are an automated debugger. specific valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                content = response.choices[0].message.content
                
            elif client_type == "anthropic":
                response = await client.messages.create(
                    model=model_name,
                    max_tokens=2000,
                    system="You are an automated debugger. return valid JSON only.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
            else:
                # Fallback
                return None
                
            # Extract JSON
            return self._extract_json(content)
            
        except Exception as e:
            if self.config.verbose:
                print(f"[Corrector] Correction failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Identify and parse JSON from text."""
        try:
            # Fast path
            return json.loads(text)
        except:
            # Look for markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                snippet = text[start:end].strip()
                try:
                    return json.loads(snippet)
                except:
                    pass
            # Look for first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
        return None
