"""
Base skill interface and protocol.

Defines the contract that all skills must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


class MissingConfigError(Exception):
    """Exception raised when a skill is missing required configuration."""
    def __init__(self, skill_name: str, missing_keys: List[str], schema: Dict[str, Any]):
        self.skill_name = skill_name
        self.missing_keys = missing_keys
        self.schema = schema
        super().__init__(f"Skill '{skill_name}' is missing required configuration: {', '.join(missing_keys)}")


@dataclass
class SkillTestCase:
    """Defines a test case for a skill."""
    input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    assertions: Optional[List[str]] = None  # Natural language assertions for the Brain
    description: str = "Test case"

@dataclass
class SkillMetadata:
    """Metadata describing a skill's capabilities."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]  # Should be a JSON Schema dict
    output_schema: Dict[str, Any]
    category: str = "general"
    version: str = "0.1.0"
    timeout: int = 30
    config_schema: Optional[Dict[str, Any]] = None  # JSON Schema for required config (API keys, etc.)
    requirements: Optional[List[str]] = None  # List of pip dependencies
    tests: Optional[List[SkillTestCase]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "category": self.category,
            "version": self.version,
            "timeout": self.timeout,
            "config_schema": self.config_schema,
            "requirements": self.requirements,
        }


class Skill(ABC):
    """
    Abstract base class for all skills.
    
    Skills are modular workers that perform specific tasks.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata:
        """Return skill metadata."""
        pass

    def __init__(self, config=None):
        self.agi_config = config
        self.config: Dict[str, Any] = {}
        self.data_dir: Optional[str] = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill.
        
        Args:
            **kwargs: Input parameters matching the input_schema
            
        Returns:
            Dictionary of outputs matching the output_schema
            
        Raises:
            Exception: If execution fails
        """
        pass
    
    async def validate_inputs(self, **kwargs):
        """
        Validate inputs before execution.
        
        Args:
            **kwargs: Input parameters
            
        Raises:
            ValueError: If validation fails
        """
    async def validate_inputs(self, **kwargs):
        """
        Validate inputs before execution.
        """
        schema = self.metadata.input_schema
        
        # Check if this is a JSON Schema (has 'properties' or 'type': 'object')
        is_json_schema = "properties" in schema or schema.get("type") == "object"
        
        if is_json_schema:
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            for param in required:
                if param not in kwargs:
                    raise ValueError(f"Missing required parameter: {param}")
            # Could add stricter type checking using jsonschema library here
        else:
            # Legacy simplified schema {param: type_str}
            for param, type_str in schema.items():
                if param not in kwargs:
                    raise ValueError(f"Missing required parameter: {param}")

    async def check_config(self):
        """
        Check if all required configuration is present.
        
        Raises:
            MissingConfigError: If configuration is missing
        """
        if not self.metadata.config_schema:
            return
            
        schema = self.metadata.config_schema
        required = schema.get("required", [])
        
        # Also treat everything in 'properties' as required if not specified?
        # Typically in these schemas, we want the user to fill them.
        # Let's check against self.config
        missing = []
        import os
        for key in required:
            # Check config dict OR environment variable
            value = self.config.get(key)
            if value is None:
                value = os.getenv(key)
            
            if not value:
                missing.append(key)
                
        if missing:
            raise MissingConfigError(self.metadata.name, missing, schema)
    
    async def pre_execute(self, **kwargs):
        """
        Hook called before execute().
        
        Can be overridden for setup logic.
        """
        pass
    
    async def post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called after execute().
        
        Can be overridden for cleanup or result transformation.
        
        Args:
            result: Raw execution result
            
        Returns:
            Transformed result
        """
        return result
