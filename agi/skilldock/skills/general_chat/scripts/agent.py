"""
General Chat foundation skill.
"""

from typing import Dict, Any, List, Optional
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase
from agi.brain import GenAIBrain, TaskType


class GeneralChatSkill(Skill):
    """
    Handles general conversational queries, greetings, and chit-chat
    using the creative/fast capabilities of the Brain.
    """
    
    def __init__(self, config):
        self.config = config
        self.brain = GenAIBrain(config)
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="general_chat",
            description="Handle general conversation, greetings, and non-technical questions",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The user's message"},
                    "history": {
                        "type": "array", 
                        "items": {"type": "object"}, 
                        "description": "Previous conversation history (optional)"
                    }
                },
                "required": ["message"]
            },
            output_schema={
                "reply": "str"
            },
            category="foundation",
            timeout=60,
            tests=[
                SkillTestCase(
                    description="Simple Greeting",
                    input={"message": "Hello there"},
                    assertions=["Reply contains a greeting"]
                )
            ]
        )
    
    async def execute(self, message: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate a conversational reply.
        """
        await self.validate_inputs(message=message)
        
        # Select appropriate model (Creative or Fast is usually best for chat)
        # We'll use CREATIVE for better personality or FAST for speed
        provider, model = self.brain.select_model(TaskType.CREATIVE) 
        client = self.brain.get_client(provider)
        
        # Build prompt/messages
        system_prompt = (
            "You are a helpful and friendly AI assistant inside the Connex AGI system. "
            "Your role is to engage in general conversation. "
            "Be concise, polite, and helpful."
        )
        
        messages = history or []
        # Convert history if needed (simplified here, assuming list of dicts with role/content)
        # For this foundation skill, we'll just append the new message
        messages.append({"role": "user", "content": message})
        
        try:
            # Revisit BrainPlanner's _call_model logic - ideally Brain should expose this method publicly
            # or we duplicate the adapter logic here for now since Brain doesn't have a unified valid 'chat' method yet.
            # To keep it simple and consistent with BrainPlanner, I'll implement a simple adapter here too.
            
            reply = await self._call_model(client, provider, model, system_prompt, messages)
            
            return {
                "reply": reply,
                "model_used": f"{provider}/{model}"
            }
            
        except Exception as e:
            return {
                "reply": f"I apologized, but I encountered an error responding: {str(e)}",
                "error": str(e)
            }

    async def _call_model(
        self, 
        client, 
        provider: str, 
        model: str, 
        system_prompt: str, 
        messages: List[Dict]
    ) -> str:
        """Adapter for different model API styles."""
        
        # OpenAI / DeepSeek / Groq (OpenAI-compatible)
        if provider in ["openai", "deepseek", "groq"]:
            # Prepend system prompt to messages
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = await client.chat.completions.create(
                model=model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        # Anthropic schema
        elif provider == "anthropic":
            # Filter out system messages from history if any, as Anthropic uses system param
            api_messages = [m for m in messages if m["role"] != "system"]
            
            response = await client.messages.create(
                model=model,
                system=system_prompt,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.content[0].text
            
        # Gemini (Direct SDK)
        elif provider == "gemini":
            # Simplified mock for Gemini currently
            model_instance = client.GenerativeModel(model)
            last_msg = messages[-1]["content"] 
            full_prompt = f"{system_prompt}\n\nUser: {last_msg}"
            response = model_instance.generate_content(full_prompt)
            return response.text
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
