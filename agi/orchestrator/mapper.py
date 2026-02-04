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
    def resolve_inputs(action, execution_state, skill=None) -> Dict[str, Any]:
        """
        Resolve all inputs for an action.
        
        Combines static inputs with dynamic references to previous outputs.
        Applies auto-mapping if skill is provided.
        """
        resolved = {}
        
        # Start with static inputs
        print( "action", action)
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
        
        # SELF-HEALING: If skill is provided, try to align resolved inputs with schema
        if skill:
            resolved = IOMapper.auto_map_to_schema(resolved, skill.metadata, action.description)
            
        return resolved

    @staticmethod
    def auto_map_to_schema(inputs: Dict[str, Any], metadata, description: str = "") -> Dict[str, Any]:
        """
        Smart mapping to bridge the gap between LLM hallucinations and strict technical contracts.
        
        1. Fuzzy Parameter Matching (e.g., 'file_path' -> 'path')
        2. Semantic Action Inference (if 'action' is missing but clear from description)
        3. Type Coercion (e.g., '123' -> 123 for integer fields)
        """
        schema = metadata.input_schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # If schema is just {key: type}, convert to properties for mapping
        if not properties and "type" not in schema:
            properties = {k: {"type": v} for k, v in schema.items()}
            required = list(properties.keys())
            
        mapped = inputs.copy()
        
        # --- 1. Fuzzy Parameter Mapping ---
        # If a required parameter is missing, check for synonyms/similar names
        missing_required = [p for p in required if p not in mapped]
        
        if missing_required:
            synonyms = {
                "path": ["file_path", "filename", "file_name", "key", "target", "uri", "location", "path_to_file"],
                "content": ["data", "text", "body", "payload", "message", "value", "content_body"],
                "action": ["operation", "op", "method", "task", "mode", "act"],
                "query": ["q", "search_term", "text", "message", "prompt", "question"],
                "message": ["text", "msg", "content", "query", "prompt", "input_text"],
                "url": ["uri", "link", "address", "website", "site"],
                "location": ["city", "place", "address", "town", "region", "target_location"]
            }
            
            for missing in missing_required:
                possible_keys = synonyms.get(missing, [])
                for alt in possible_keys:
                    if alt in mapped:
                        mapped[missing] = mapped[alt]
                        break

        # --- 2. Semantic Action Inference ---
        # If 'action' or 'operation' is missing but the schema defines it with an enum
        target_action_key = "action" if "action" in properties else ("operation" if "operation" in properties else None)
        
        if target_action_key and target_action_key not in mapped and description:
            prop_def = properties.get(target_action_key, {})
            enum_values = prop_def.get("enum", [])
            
            if enum_values:
                # Try to find a keyword match in the description
                desc_lower = description.lower()
                for val in enum_values:
                    # Match 'read_file' if description has 'read'
                    # Or 'storage' if description has 'store'
                    stem = val.lower().split('_')[0]
                    if len(stem) > 3 and stem in desc_lower:
                        mapped[target_action_key] = val
                        break

        # --- 3. Type Coercion ---
        for key, value in mapped.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "integer" and isinstance(value, str) and value.isdigit():
                    mapped[key] = int(value)
                elif expected_type == "boolean" and isinstance(value, str):
                    if value.lower() in ["true", "yes", "1", "on"]: mapped[key] = True
                    elif value.lower() in ["false", "no", "0", "off"]: mapped[key] = False
                elif expected_type == "string" and not isinstance(value, str):
                    # Auto-stringify lists/dicts if string is expected
                    if isinstance(value, (list, dict)):
                        mapped[key] = json.dumps(value, indent=2)
                    else:
                        mapped[key] = str(value)
                    
        return mapped
    
    @staticmethod
    def validate_output(output: Dict[str, Any], expected_schema: Dict[str, Any], action_id: str = "unknown") -> Dict[str, Any]:
        """
        Validate and SMART-MAP output to match the expected schema.
        
        Args:
            output: Actual output from the action
            expected_schema: Expected schema
            action_id: ID for logging
            
        Returns:
            Mapped output dictionary
        """
        if not output:
             return {"success": False, "error": "Skill returned null or empty output"}

        # If the skill explicitly failed, we don't enforce the full schema
        if output.get("success") is False:
            return output

        if not expected_schema:
            return output

        mapped_output = output.copy()
        
        # 1. Normailize target keys from schema
        target_keys = {}
        if isinstance(expected_schema, dict) and "properties" in expected_schema:
            # It's a JSON Schema
            for name, prop in expected_schema["properties"].items():
                target_keys[name] = prop.get("type", "any")
        elif isinstance(expected_schema, dict) and "type" in expected_schema and len(expected_schema) <= 2:
            # Whole thing is a certain type (generic)
            pass
        elif isinstance(expected_schema, dict):
            # Simple mapping
            target_keys = expected_schema
            
        # 2. Validate and Map
        for key, type_str in target_keys.items():
            if key not in mapped_output:
                # --- SMART OUTPUT MAPPING ---
                synonyms = {
                    "content": ["data", "text", "body", "file_content", "result", "message"],
                    "reply": ["response", "answer", "text", "message", "output"],
                    "status": ["success", "message", "result", "state"]
                }
                
                found = False
                for alt in synonyms.get(key, []):
                    if alt in mapped_output:
                        mapped_output[key] = mapped_output[alt]
                        found = True
                        break
                
                if not found:
                    # Log as warning instead of raising (Leinent validation as requested)
                    if not any(k in mapped_output for k in ["success", "error", "message"]):
                        print(f"[IOMapper] WRN: Action {action_id} missing expected key '{key}'. "
                              f"Actual keys: {list(mapped_output.keys())}")
                    # We don't raise here to allow execution to proceed if possible
                    continue
            
            # Basic type checking (with coercion if possible)
            value = mapped_output[key]
            # type_str might be a dict if it's a nested JSON schema, skip check for those
            if not isinstance(type_str, str):
                continue
                
            if not IOMapper._check_type(value, type_str):
                try:
                    if type_str == "str": mapped_output[key] = str(value)
                    elif type_str == "int": mapped_output[key] = int(value)
                    elif type_str == "float": mapped_output[key] = float(value)
                except:
                    # Warn instead of raise
                    print(f"[IOMapper] WRN: Key '{key}' type mismatch. Expected {type_str}, got {type(value).__name__}")
        
        return mapped_output
    
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
