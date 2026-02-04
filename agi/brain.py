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

    async def reason(self, goal: str, context: Optional[Dict[str, Any]] = None):
        """
        Perform a reasoning analysis of the goal.
        
        Yields reasoning tokens or progress updates.
        """
        provider, model = self.select_model(TaskType.PLANNING)
        client = self.get_client(provider)
        
        if self.config.verbose:
            print(f"[Brain] Reasoning with {provider}/{model}...")
        
        # Load Constitution (The Soul)
        soul_path = os.path.join(os.path.dirname(__file__), "SOUL.md")
        soul_content = ""
        if os.path.exists(soul_path):
            with open(soul_path, "r") as f:
                soul_content = f.read()

        prompt = f"""You are the 'Reasoning Engine' of an autonomous AGI.
        Your goal is to analyze the user's request and devise a robust, efficient strategy.
        
        ### CONNECTED CONSTITUTION (THE SOUL)
        You MUST adhere to the following principles:
        {soul_content}
        ### END CONSTITUTION

        Goal: "{goal}"
        Context: {json.dumps(context or {})}

        Perform a deep 'Inner Monologue' before taking action. Structured your thoughts:
        1. **Core Objective**: What does the user *actually* want? (Interpret intent beyond words)
        2. **Capability Check**: Which specific skills/tools are best suited? (e.g., 'browser' for research, 'code_executor' for calc)
        3. **Constraint Analysis**: Are there missing inputs? Risks? API limits? Ambiguities?
        4. **Strategic Plan**:
           - Step 1: ...
           - Step 2: ...
           - Self-Correction Strategy: "If Step 1 fails, I will..."

        Be proactive. If the goal is vague, decide on the most logical path rather than just asking for clarification (unless critical).
        """
        
        try:
            if provider in ["openai", "deepseek", "groq"]:
                stream = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt    }],
                    temperature=0.3,
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield {
                            "type": "reasoning_token",
                            "token": chunk.choices[0].delta.content
                        }
            elif provider == "anthropic":
                # Anthropic streaming
                async with client.messages.stream(
                    model=model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    async for text in stream.text_stream:
                        yield {
                            "type": "reasoning_token",
                            "token": text
                        }
        except Exception as e:
            print(f"[Brain] Reasoning failed: {e}")
            yield {"type": "reasoning_error", "error": str(e)}

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

    async def classify_intent(self, query: str) -> str:
        """
        Classify the user intent into CHAT or ACTION.
        
        CHAT: Simple greetings, general questions, or conversational filler.
        ACTION: Requests that imply performing a task, searching, or using tools.
        """
        provider, model = self.select_model(TaskType.FAST)
        client = self.get_client(provider)
        
        prompt = f"""Classify the user's intent as either 'CHAT' or 'ACTION'.
        
        'CHAT': Greetings, personal questions about the AI, general knowledge questions that don't need tools, or simple conversation.
        'ACTION': Requests to do something, search the web, analyze data, execute code, manage files, or create something.
        
        User Query: "{query}"
        
        Respond ONLY with 'CHAT' or 'ACTION'.
        """
        
        try:
            if provider in ["openai", "deepseek", "groq"]:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=10
                )
                intent = response.choices[0].message.content.strip().upper()
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=10
                )
                intent = response.content[0].text.strip().upper()
            else:
                # Fallback for other providers
                intent = "ACTION"
                
            return "CHAT" if "CHAT" in intent else "ACTION"
        except Exception as e:
            print(f"[Brain] Intent classification failed: {e}")
            return "ACTION"  # Default to ACTION for safety

    def _get_default_provider_and_model(self) -> tuple[str, str]:
        """Recursive fallback for defaults."""
        if self.config.default_executor:
            return self.config.default_executor, self.config.executor_model
        
        if self.config.openai_api_key:
            return "openai", "gpt-4o"
        
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

