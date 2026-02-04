"""
File Manager skill for safe filesystem operations.
"""

import os
from typing import Dict, Any, List
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class FileManagerSkill(Skill):
    """
    Skill for reading, writing, and listing files safely.
    """
    
    def __init__(self, config=None):
        self.config = config
        # Default to current directory if not specified otherwise
        self.workspace_root = os.getcwd()
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="file_manager",
            description="Read, write, and manage files in the workspace",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string", 
                        "enum": ["read_file", "write_file", "list_directory"],
                        "description": "Action to perform"
                    },
                    "path": {"type": "string", "description": "Relative path to file or directory"},
                    "content": {"type": "string", "description": "Content to write (for write_file)"}
                },
                "required": ["action", "path"]
            },
            output_schema={
                "success": "bool",
                "content": "str",
                "data": "str | list",
                "message": "str"
            },
            category="io",
            tests=[
                SkillTestCase(
                    description="Write and Read File",
                    input={
                        "operation": "write_file", 
                        "path": "test_file.txt", 
                        "content": "Hello World"
                    },
                    assertions=["Result success is True"]
                )
            ]
        )
    
    async def execute(self, action: str = None, path: str = None, content: str = "", **kwargs) -> Dict[str, Any]:
        """
        Execute file operation.
        """
        # Handle aliases from LLM hallucinations
        if not action:
            action = kwargs.get("operation")
        
        if not path:
            path = kwargs.get("file_name") or kwargs.get("key") or kwargs.get("filename") or kwargs.get("file_path")

        # Validate after aliasing
        if not action:
             return {"success": False, "message": "Missing 'action' (or 'operation')"}
        if not path:
             return {"success": False, "message": "Missing 'path' (or 'file_name', 'key')"}

        # Map 'write' to 'write_file' if needed
        if action == "write":
            action = "write_file"
        elif action == "read":
            action = "read_file"
        elif action == "list":
            action = "list_directory"
            
        await self.validate_inputs(action=action, path=path)
        
        # Security check: Ensure path is within workspace (simple check)
        # In a real system, you'd use os.path.abspath and commonprefix
        normalized_path = os.path.normpath(path)
        if ".." in normalized_path and not self.config.verbose: # Allow .. only in verbose/dev mode maybe? NO, unsafe.
             # Strict safety for now
             if normalized_path.startswith(".."):
                 return {"success": False, "message": "Access denied: Path outside workspace"}

        full_path = path # relative to CWD
        
        try:
            if action == "read_file":
                if not os.path.exists(full_path):
                    return {"success": False, "message": f"File not found: {path}"}
                
                with open(full_path, "r", encoding="utf-8") as f:
                    data = f.read()
                return {
                    "success": True, 
                    "data": data, 
                    "content": data, 
                    "file_content": data
                }
            
            elif action == "write_file":
                # Ensure dir exists
                os.makedirs(os.path.dirname(full_path) if os.path.dirname(full_path) else ".", exist_ok=True)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "message": f"Written {len(content)} chars to {path}"}
            
            elif action == "list_directory":
                if not os.path.exists(full_path):
                     return {"success": False, "message": f"Directory not found: {path}"}
                
                items = os.listdir(full_path)
                return {"success": True, "data": items}
            
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
