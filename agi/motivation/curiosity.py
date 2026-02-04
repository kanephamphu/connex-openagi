
from typing import List, Dict, Any, Optional
import random
from agi.brain import GenAIBrain, TaskType

class CuriosityModule:
    """
    Generates intrinsic motivation (curiosity) goals when the agent is idle.
    """
    
    def __init__(self, config, brain: GenAIBrain):
        self.config = config
        self.brain = brain
        # Base interests to seed the curiosity
        self.interests = [
            "Advanced Python capabilities",
            "System optimization algorithms",
            "Machine Learning concepts",
            "New AGI cognitive architectures",
            "Data structure efficiency"
        ]
        
    async def propose_goal(self, context_summary: str = "") -> Dict[str, Any]:
        """
        Proposes a new goal based on intrinsic interests and recent context.
        """
        # Pick a random interest to focus on
        focus_topic = random.choice(self.interests)
        
        prompt = f"""
        You are the 'Curiosity' module of an AGI.
        The system is currently idle. Propose a short, safe, and interesting task to perform to improve capabilities or knowledge.
        
        Focus Topic: {focus_topic}
        Context: {context_summary}
        
        The task must be achievable within the agent's environment (Mac, Python).
        Avoid dangerous actions. Pondering or researching code patterns is good.
        
        Response Format (JSON):
        {{
            "goal": "Short title of the goal",
            "description": "One sentence description of what to do.",
            "rationale": "Why this is interesting or useful.",
            "type": "research" or "practice"
        }}
        """
        
        try:
            provider, model = self.brain.select_model(TaskType.PLANNING)
            client = self.brain.get_client(provider)
            
            # Helper for simple generation using the existing client setup
            # We reuse the logic from Evaluator essentially, maybe should be a utility in Brain
            if provider in ["openai", "deepseek", "groq"]:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7, # Higher temp for creativity
                    response_format={"type": "json_object"} if provider != "groq" else None
                )
                content = response.choices[0].message.content
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                content = response.content[0].text
            else:
                # Fallback for mock/other
                return {
                    "goal": f"Study {focus_topic}",
                    "description": f"Read documentation about {focus_topic}",
                    "rationale": "Fallback generation.",
                    "type": "research"
                }
                
            return self._parse_json(content)
            
        except Exception as e:
            if self.config.verbose:
                print(f"[Curiosity] Failed to generate proposal: {e}")
            return None

    def _parse_json(self, text: str) -> Dict[str, Any]:
        import json
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return {"goal": "Explore", "description": "Just looking around", "type": "research"}
