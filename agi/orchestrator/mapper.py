"""
Input/Output mapping logic for the orchestrator.

Handles schema validation and data transformation between action steps.
"""

from typing import Any, Dict
import json


class IOMapper:
    """
    Maps inputs and outputs between actions.
    
    Handles type conversion and validation.
    """
    
    @staticmethod
    def resolve_inputs(action, execution_state) -> Dict[str, Any]:
        """
        Resolve all inputs for an action.
        
        Combines static inputs with dynamic references to previous outputs.
        
        Args:
            action: ActionNode to resolve inputs for
            execution_state: Current execution state
            
        Returns:
            Dictionary of resolved input values
            
        Raises:
            ValueError: If a reference cannot be resolved
        """
        resolved = {}
        
        # Start with static inputs
        resolved.update(action.inputs)
        
        # Auto-resolve inline references in inputs (e.g. "action_1.result")
        for key, value in action.inputs.items():
            if isinstance(value, str) and value.startswith("action_") and "." in value:
                try:
                    resolved_val = execution_state.get_output(value)
                    resolved[key] = resolved_val
                except Exception:
                    # If resolution fails, keep as string (might be intentional)
                    pass
        
        # Resolve explicit input references (overrides inline)
        for param_name, reference in action.input_schema.items():
            try:
                value = execution_state.get_output(reference)
                resolved[param_name] = value
            except KeyError:
                raise ValueError(
                    f"Action {action.id}: Cannot resolve input reference '{reference}'"
                )
        
        return resolved
    
    @staticmethod
    def validate_output(output: Dict[str, Any], expected_schema: Dict[str, Any]) -> bool:
        """
        Validate that an output matches the expected schema.
        
        Args:
            output: Actual output from the action
            expected_schema: Expected schema (e.g., {'results': 'List[dict]'})
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        for key, type_str in expected_schema.items():
            if key not in output:
                raise ValueError(f"Missing expected output key: {key}")
            
            # Basic type checking
            value = output[key]
            if not IOMapper._check_type(value, type_str):
                raise ValueError(
                    f"Output key '{key}' has incorrect type. "
                    f"Expected {type_str}, got {type(value).__name__}"
                )
        
        return True
    
    @staticmethod
    def _check_type(value: Any, type_definition: Any) -> bool:
        """
        Basic type checking for common types.
        
        Args:
            value: Value to check
            type_definition: Type string like 'str' OR complex schema dict
            
        Returns:
            True if type matches
        """
        # If schema is a dictionary or not a string, we skip simple type checking
        if not isinstance(type_definition, str):
            return True

        type_str = type_definition
        
        # Simple type mapping
        if type_str == "str":
            return isinstance(value, str)
        elif type_str == "int":
            return isinstance(value, int)
        elif type_str == "float":
            return isinstance(value, (int, float))
        elif type_str == "bool":
            return isinstance(value, bool)
        elif type_str == "dict":
            return isinstance(value, dict)
        elif type_str == "list" or type_str.startswith("List["):
            return isinstance(value, list)
        elif type_str == "Any":
            return True
        
        # Default to True for complex types we can't easily validate
        return True
    
    @staticmethod
    def format_output_for_display(output: Dict[str, Any], max_length: int = 200) -> str:
        """
        Format output for human-readable display.
        
        Args:
            output: Output dictionary
            max_length: Maximum length to display
            
        Returns:
            Formatted string
        """
        try:
            formatted = json.dumps(output, indent=2)
            if len(formatted) > max_length:
                return formatted[:max_length] + "..."
            return formatted
        except:
            return str(output)[:max_length]
