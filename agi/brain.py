"""
The GenAI Brain: Centralized intelligence for model selection and routing.

This module abstracts the complexity of multiple LLM providers, allowing the AGI
to dynamically select the best model for a given task (reasoning, coding, creative).
"""

import os
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Literal

from agi.config import AGIConfig


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    GEMINI = "gemini"


class TaskType(str, Enum):
    PLANNING = "planning"      # Requires high reasoning (e.g., DeepSeek-R1, o1)
    CODING = "coding"          # Requires strong coding capability (e.g., Claude 3.5, GPT-4o)
    CREATIVE = "creative"      # Requires good writing (e.g., Claude 3 Opus, GPT-4o)
    FAST = "fast"              # Requires speed (e.g., Groq/Llama-3, GPT-3.5)
    GENERAL = "general"        # Balanced choice


class GenAIBrain:
    """
    Central intelligence unit for the AGI.
    
    Manages connections to multiple AI providers and routes tasks to the
    most appropriate model based on capability and configuration.
    """
    
    def __init__(self, config: AGIConfig):
        self.config = config
        self._clients: Dict[str, Any] = {}
        
    def get_client(self, provider: str | Provider) -> Any:
        """
        Get or initialize a client for the specified provider.
        """
        provider_name = str(provider).lower()
        
        if provider_name in self._clients:
            return self._clients[provider_name]
        
        client = self._initialize_client(provider_name)
        self._clients[provider_name] = client
        return client
        
    def _initialize_client(self, provider: str) -> Any:
        """Initialize a specific provider client."""
        if provider == "openai":
            if not self.config.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.config.openai_api_key)
            
        elif provider == "deepseek":
            if not self.config.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key=self.config.deepseek_api_key,
                base_url=self.config.deepseek_api_base
            )
            
        elif provider == "anthropic":
            if not self.config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=self.config.anthropic_api_key)
            
        elif provider == "groq":
            if not self.config.groq_api_key:
                raise ValueError("GROQ_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key=self.config.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
        elif provider == "gemini":
            if not self.config.google_api_key:
                raise ValueError("GOOGLE_API_KEY not configured")
            # Using Google's GenAI SDK
            import google.generativeai as genai
            genai.configure(api_key=self.config.google_api_key)
            return genai
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def reason(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform strategic reasoning to identify required capabilities.
        
        Returns:
            {
                "refined_goal": str,
                "required_capabilities": List[str],
                "reasoning": str
            }
        """
        provider, model = self.select_model(TaskType.PLANNING)
        client = self.get_client(provider)
        
        if self.config.verbose:
            print(f"[Brain] Strategic reasoning with {provider}/{model}...")
        
        # Load Constitution (The Soul)
        soul_path = os.path.join(os.path.dirname(__file__), "SOUL.md")
        soul_content = ""
        if os.path.exists(soul_path):
            with open(soul_path, "r") as f:
                soul_content = f.read()

        prompt = f"""You are the 'Strategic Reasoning Engine' of an autonomous AGI.
Your task is to analyze the user's goal and identify what capabilities (skills/perceptions) are needed.

### CONNECTED CONSTITUTION (THE SOUL)
You MUST adhere to the following principles:
{soul_content}
### END CONSTITUTION

Goal: "{goal}"
Context: {json.dumps(context or {})}

### EMOTIONAL CONTEXT
Detected User Emotion: {context.get('human_emotion', 'neutral') if context else 'neutral'}
AGI Self-Reflection: {context.get('agi_emotion', 'neutral') if context else 'neutral'}

### CONVERSATION CONTEXT
Summary: {context.get('conversation_summary', 'None') if context else 'None'}
Recent Turns: {json.dumps(context.get('conversation_history', [])[:3]) if context else '[]'}

### NOTABLE INFORMATION
User Knowledge: {json.dumps(context.get('notable_information', {}) if context else {})}

### YOUR TASK
Analyze this goal and identify:
1. **Refined Goal**: A clearer, more actionable version of the user's request
2. **Required Capabilities**: List of skill/perception names that would help (e.g., "web search", "file manager", "weather api")
   - Think about: What tools/sensors are needed?
   - Be specific but don't invent capabilities
3. **Reasoning**: Brief explanation of your analysis

Output ONLY valid JSON:
{{
  "refined_goal": "Clear, actionable goal statement",
  "required_capabilities": ["capability_1", "capability_2"],
  "reasoning": "Brief explanation of why these capabilities are needed"
}}
"""
        
        try:
            if provider in ["openai", "deepseek", "groq"]:
                kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a strategic reasoning engine. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1,
                }
                
                try:
                    response = await client.chat.completions.create(**kwargs)
                except Exception as e:
                    # Robust parameter retry
                    retry_needed = False
                    err_str = str(e).lower()
                    if "max_tokens" in err_str and "supported" in err_str:
                        kwargs.pop("max_tokens", None)
                        kwargs["max_completion_tokens"] = 800
                        retry_needed = True
                    if "temperature" in err_str and ("supported" in err_str or "value" in err_str):
                        kwargs["temperature"] = 1.0
                        retry_needed = True
                    
                    if retry_needed:
                        response = await client.chat.completions.create(**kwargs)
                    else:
                        raise
                
                result_text = response.choices[0].message.content.strip()
                
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    max_tokens=800,
                    system="You are a strategic reasoning engine. Respond ONLY with valid JSON.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text.strip()
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Parse JSON
            if self.config.verbose:
                print(f"[Brain] Raw reasoning response: {result_text}")
            
            # Clean potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(result_text)
            
            # Validate structure
            if not all(k in parsed for k in ["refined_goal", "required_capabilities", "reasoning"]):
                raise ValueError("Missing required keys in reasoning output")
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"[Brain] JSON parsing failed: {e}. Raw: {result_text}")
            # Fallback
            return {
                "refined_goal": goal,
                "required_capabilities": [],
                "reasoning": "Failed to parse reasoning output"
            }
        except Exception as e:
            print(f"[Brain] Reasoning failed: {e}")
            return {
                "refined_goal": goal,
                "required_capabilities": [],
                "reasoning": f"Error: {str(e)}"
            }


    def select_model(self, task_type: TaskType | str) -> tuple[str, str]:
        """
        Select the best provider and model for a given task.
        
        Returns:
            (provider_name, model_name)
        """
        task = TaskType(task_type)
        
        # 1. PLANNING (High Reasoning)
        if task == TaskType.PLANNING:
            # Honor configured planner model if applicable to the provider
            custom_model = self.config.planner_model
            
            if self.config.deepseek_api_key and self.config.default_planner == "deepseek":
                return "deepseek", custom_model or "deepseek-reasoner"
            elif self.config.openai_api_key and self.config.default_planner == "openai":
                return "openai", custom_model or "gpt-4o"
            elif self.config.anthropic_api_key and self.config.default_planner == "anthropic":
                return "anthropic", custom_model or "claude-3-5-sonnet-20240620"
            
            # Fallback to defaults if specific planner not set but keys available
            if self.config.deepseek_api_key:
                return "deepseek", "deepseek-reasoner"
            elif self.config.openai_api_key:
                return "openai", "gpt-4o"
            elif self.config.anthropic_api_key:
                return "anthropic", "claude-3-5-sonnet-20240620"
                
        # 2. CODING (High Precision)
        elif task == TaskType.CODING:
            if self.config.anthropic_api_key:
                return "anthropic", "claude-3-5-sonnet-20240620"
            elif self.config.openai_api_key:
                return "openai", "gpt-4o"
            elif self.config.deepseek_api_key:
                return "deepseek", "deepseek-coder"
                
        # 3. FAST (Speed priority)
        elif task == TaskType.FAST:
            if self.config.groq_api_key:
                return "groq", "llama3-70b-8192"
            elif self.config.openai_api_key:
                return "openai", "gpt-3.5-turbo"
        
        # Default fallback
        return self._get_default_provider_and_model()

    def _get_default_provider_and_model(self) -> tuple[str, str]:
        """Recursive fallback for defaults."""
        if self.config.default_executor:
            return self.config.default_executor, self.config.executor_model
        
        if self.config.openai_api_key:
            return "openai", "gpt-5-nano"
        
        raise ValueError("No default provider configured. Please set OPENAI_API_KEY or default_executor.")

    async def classify_intent_fast(self, query: str, context: Optional[Dict[str, Any]] = None, sub_brain_manager: Optional[Any] = None) -> tuple[str, Dict[str, Any]]:
        """
        Wrapper for unified intent classification.
        """
        return await self.classify_intent(query, context, sub_brain_manager)

    async def classify_intent(self, query: str, context: Optional[Dict[str, Any]] = None, sub_brain_manager: Optional[Any] = None) -> tuple[str, Dict[str, Any]]:
        """
        Classify the user intent into core categories.
        Supports CHAT, RESEARCH, SINGLE_ACTION, PLAN.
        
        Returns:
            (intent_string, notable_information_dict)
        """
        # 1. Routing Decision: Always prefer Sub-Brain Manager if available (it handles both local and external configs)
        target_brain = sub_brain_manager
        
        # Prepare Context
        summary = (context or {}).get('summary', 'None')
        history_raw = (context or {}).get('recent_history', [])
        history = json.dumps(history_raw[:-5] if len(history_raw) > 5 else history_raw)

        # 2. Unified Prompt
        prompt_text = (
                "### INTENT CLASSIFICATION & INFORMATION EXTRACTION\n"
                "You are a high-precision Intent Classifier. Your goal is to map user input to the correct processing tier AND extract notable information.\n\n"
                "### CATEGORIES\n"
                "1. CHAT: Social interactions, greetings, bot identity, or simple acknowledgement.\n"
                "2. RESEARCH: Knowledge lookups, news, weather, or finding facts online.\n"
                "3. SINGLE_ACTION: One-off system/file commands (opening apps, volume, file management).\n"
                "4. PLAN: Multi-step goals, data synthesis, or complex problem solving.\n\n"
                "### NOTABLE INFORMATION\n"
                "1. New Info: Extract specific entities/preferences the user provides (e.g., 'my name is X'). Key-Value pair.\n"
                "2. Retrieval & Relevance: Extract keys for information that is requested OR logically relevant to the request. Set value to EMPTY string (\"\").\n"
                "   - Direct: 'what is my API key?' -> {\"api_key\": \"\"}\n"
                "   - Associative: 'How is my family?' -> {\"mom_name\": \"\", \"dad_name\": \"\", \"family_members\": \"\"}\n"
                "   - Contextual: 'Deploy this' -> {\"aws_credentials\": \"\", \"github_token\": \"\"}\n"
                "Format: {\"intent\": \"...\", \"notable_information\": {\"key\": \"value_or_empty\"}}\n"
                "If no notable info, return empty dict.\n\n"
                "### EXAMPLES\n"
                "- \"Hey there\" -> {\"intent\": \"CHAT\", \"notable_information\": {}}\n"
                "- \"Find news about Apple\" -> {\"intent\": \"RESEARCH\", \"notable_information\": {}}\n"
                "- \"My mom's phone number is 555-0199\" -> {\"intent\": \"CHAT\", \"notable_information\": {\"mom_phone\": \"555-0199\"}}\n"
                "- \"What is my mom's phone number?\" -> {\"intent\": \"CHAT\", \"notable_information\": {\"mom_phone\": \"\"}}\n"
                "- \"I save my API key as sk-123\" -> {\"intent\": \"SINGLE_ACTION\", \"notable_information\": {\"api_key\": \"sk-123\"}}\n"
                "- \"Use my personal API key\" -> {\"intent\": \"PLAN\", \"notable_information\": {\"personal_api_key\": \"\"}}\n\n"
                "### CONTEXT\n"
                f"Summary: {summary}\n"
                f"History: {history}\n"
                f"USER INPUT: \"{query}\"\n"
                "DECISION (JSON ONLY):"
            )

        result_raw = ""
        
        # 3. Try Sub-Brain Manager
        if target_brain:
            try:
                task = {
                    "prompt": prompt_text,
                    "system": "Respond ONLY with valid JSON containing \"intent\" and \"notable_information\"."
                }
                
                results = await target_brain.execute_parallel([task])
                if results and results[0]:
                    result_raw = results[0].strip()
            except Exception as e:
                if self.config.verbose:
                    print(f"[Brain] Sub-brain intent classification error: {e}")
                pass # Fallback to cloud

        # 4. Cloud Fallback (if sub-brain missing or failed)
        if not result_raw or result_raw == "{}":
            provider, model = self.select_model(TaskType.FAST)
            client = self.get_client(provider)
            
            system_instruction = "Respond ONLY with valid JSON containing \"intent\" and \"notable_information\"."
            
            try:
                if provider in ["openai", "deepseek", "groq"]:
                    kwargs = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt_text}
                        ],
                        "temperature": 0,
                        "max_tokens": 300  # Increased for notable info extraction
                    }
                    
                    try:
                        response = await client.chat.completions.create(**kwargs)
                    except Exception as e:
                        # Robust parameter retry
                        retry_needed = False
                        err_str = str(e).lower()
                        if "max_tokens" in err_str and "supported" in err_str:
                            kwargs.pop("max_tokens", None)
                            kwargs["max_completion_tokens"] = 300
                            retry_needed = True
                        if "temperature" in err_str and ("supported" in err_str or "value" in err_str):
                            kwargs["temperature"] = 1.0
                            retry_needed = True
                        
                        if retry_needed:
                            response = await client.chat.completions.create(**kwargs)
                        else:
                            raise e

                    result_raw = response.choices[0].message.content.strip()
                    
                elif provider == "anthropic":
                    response = await client.messages.create(
                        model=model,
                        system=system_instruction,
                        messages=[{"role": "user", "content": prompt_text}],
                        temperature=0,
                        max_tokens=150
                    )
                    result_raw = response.content[0].text.strip()
                else:
                    return "PLAN", {}
            
            except Exception as e:
                print(f"[Brain] Cloud intent classification failed: {e}")
                return "PLAN", {}

        # 5. Process Result (Unified Parser)
        try:
            # Clean up markdown
            if "```" in result_raw:
                parts = result_raw.split("```")
                if len(parts) > 1:
                    result_raw = parts[1].strip()
                    if result_raw.startswith("json"):
                        result_raw = result_raw[4:].strip()
            
            if self.config.verbose:
                print(f"[Brain] Raw Intent Response: {result_raw}")

            parsed = json.loads(result_raw)
            intent_raw = parsed.get("intent", "PLAN").upper()
            notable_info = parsed.get("notable_information", {})
            
            # Store notable info to DB if present
            if notable_info:
                try:
                    from agi.utils.database import DatabaseManager
                    db = DatabaseManager()
                    for k, v in notable_info.items():
                        if v: # Only save explicit values
                            db.set_notable_info(k, v)
                            if self.config.verbose:
                                print(f"[Brain] Stored notable info: {k}={v}")
                except Exception as db_e:
                    print(f"[Brain] Notable info DB error: {db_e}")
            
            # Normalize Intent
            valid_intents = ["CHAT", "RESEARCH", "SINGLE_ACTION", "PLAN"]
            final_intent = "PLAN"
            for i in valid_intents:
                if i in intent_raw:
                    final_intent = i
                    break
            
            return final_intent, notable_info

        except (json.JSONDecodeError, Exception) as parse_err:
            if self.config.verbose:
                    print(f"[Brain] JSON Decode Error on intent: {result_raw}")
            
            # Fallback: Try to salvage simple string intent
            intent_raw = result_raw.upper()
            valid_intents = ["CHAT", "RESEARCH", "SINGLE_ACTION", "PLAN"]
            for i in valid_intents:
                if i in intent_raw:
                    return i, {}
            
            return "PLAN", {}

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text.
        
        Prioritizes OpenAI's text-embedding-3-small for best cost/performance.
        """
        # 1. Try OpenAI
        if self.config.openai_api_key:
            client = self.get_client("openai")
            try:
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"[Brain] OpenAI Embedding failed: {e}")
        
        # 2. Try DeepSeek (if they support embeddings compatible via OpenAI SDK)
        # DeepSeek API often compatible, let's try if OpenAI failed or not present
        if self.config.deepseek_api_key:
            # Note: Specific model name for DeepSeek embeddings might differ or not exist publicly yet
            # We'll skip for now to avoid errors unless confirmed.
            pass
            
        raise ValueError("No embedding provider configured. Please set OPENAI_API_KEY.")
