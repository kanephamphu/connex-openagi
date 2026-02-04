"""
Configuration management for the AGI system.

Handles API key loading, model selection, and client factory functions.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from dotenv import load_dotenv

# Load .env file from agi directory
_agi_dir = Path(__file__).parent.parent
load_dotenv(_agi_dir / ".env")


PlannerType = Literal["deepseek", "openai", "anthropic", "gemini"]
ExecutorType = Literal["openai", "anthropic", "groq", "gemini"]


@dataclass
class AGIConfig:
    """
    Central configuration for the AGI system.
    
    Manages API keys, model selection, and runtime parameters.
    """
    
    # API Keys
    deepseek_api_key: str | None = None
    deepseek_api_base: str = "https://api.deepseek.com"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    google_api_key: str | None = None
    
    # Model Selection
    default_planner: PlannerType = "deepseek"
    default_executor: ExecutorType = "openai"
    
    # Runtime Configuration
    verbose: bool = False
    max_retries: int = 3
    action_timeout: int = 60
    self_correction_enabled: bool = True
    is_speaking: bool = False  # NEW: Global flag to prevent self-triggering via Mic
    on_speak_callback: Optional[Any] = None # NEW: Callback for echo cancellation
    
    # Model-specific settings
    planner_model: str = "deepseek-reasoner"
    executor_model: str = "gpt-4.1-nano"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Registry Configuration
    registry_url: str = "http://localhost:8000/api/v1"
    connex_auth_token: str | None = None
    skills_storage_path: str = "installed_skills"
    
    # Enable/Disable features
    allow_skill_publishing: bool = False
    allow_skill_isolation: bool = False
    skills_data_path: str = "skill_data"
    data_dir: str = "data"
    perception_storage_path: str = "installed_perception"
    reflex_storage_path: str = "installed_reflex"
    
    @classmethod
    def from_env(cls) -> "AGIConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            AGIConfig instance populated from .env file
        """
        instance = cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            deepseek_api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            
            registry_url=os.getenv("CONNEX_REGISTRY_URL", "http://localhost:8000/api/v1"),
            connex_auth_token=os.getenv("CONNEX_AUTH_TOKEN"),
            skills_storage_path=os.getenv("AGI_SKILLS_STORAGE", "installed_skills"),
            allow_skill_publishing=os.getenv("AGI_ALLOW_PUBLISHING", "false").lower() == "true",
            allow_skill_isolation=os.getenv("AGI_ISOLATE_SKILLS", "false").lower() == "true",
            skills_data_path=os.getenv("AGI_SKILLS_DATA", "skill_data"),
            
            default_planner=os.getenv("AGI_DEFAULT_PLANNER", "deepseek"),
            default_executor=os.getenv("AGI_DEFAULT_EXECUTOR", "openai"),
            planner_model=os.getenv("AGI_PLANNER_MODEL") or os.getenv("MODEL_NAME") or "gpt-4o",
            executor_model=os.getenv("AGI_EXECUTOR_MODEL") or os.getenv("MODEL_NAME") or "gpt-4o",
            verbose=os.getenv("AGI_VERBOSE", "false").lower() == "true",
            max_retries=int(os.getenv("AGI_MAX_RETRIES", "3")),
            action_timeout=int(os.getenv("AGI_ACTION_TIMEOUT", "60")),
            self_correction_enabled=os.getenv("AGI_SELF_CORRECTION_ENABLED", "true").lower() == "true",
            data_dir=os.getenv("AGI_DATA_DIR", "data"),
            perception_storage_path=os.getenv("AGI_PERCEPTION_STORAGE", "installed_perception"),
            reflex_storage_path=os.getenv("AGI_REFLEX_STORAGE", "installed_reflex"),
        )
        
        # Load overlays from Database
        try:
            from agi.utils.database import DatabaseManager
            db = DatabaseManager()
            db_config = db.get_all_config()
            
            # Apply DB overrides
            for key, value in db_config.items():
                if hasattr(instance, key) and value is not None:
                    # Convert types if necessary (DB stores JSON/Strings)
                    # For now assume mostly compatible or string
                    setattr(instance, key, value)
        except Exception as e:
            # Fallback if DB fails (e.g. migration issue or locked)
            pass
            
        return instance
    
    def get_planner_client(self, planner_type: PlannerType | None = None):
        """
        Create an LLM client for the planner tier.
        
        Args:
            planner_type: Type of planner to use. Defaults to configured default.
            
        Returns:
            Configured LLM client
            
        Raises:
            ValueError: If API key is not configured for the selected planner
        """
        planner = planner_type or self.default_planner
        
        if planner == "deepseek":
            if not self.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key=self.deepseek_api_key,
                base_url=self.deepseek_api_base
            )
        
        elif planner == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.openai_api_key)
        
        elif planner == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=self.anthropic_api_key)
        
        elif planner == "gemini":
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY not configured")
            # Google Gemini client would go here
            raise NotImplementedError("Gemini support coming soon")
        
        raise ValueError(f"Unknown planner type: {planner}")
    
    def get_executor_client(self, executor_type: ExecutorType | None = None):
        """
        Create an LLM client for execution tasks.
        
        Args:
            executor_type: Type of executor to use. Defaults to configured default.
            
        Returns:
            Configured LLM client
            
        Raises:
            ValueError: If API key is not configured for the selected executor
        """
        executor = executor_type or self.default_executor
        
        if executor == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.openai_api_key)
        
        elif executor == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=self.anthropic_api_key)
        
        elif executor == "groq":
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY not configured")
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key=self.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        
        elif executor == "gemini":
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY not configured")
            raise NotImplementedError("Gemini support coming soon")
        
        raise ValueError(f"Unknown executor type: {executor}")
