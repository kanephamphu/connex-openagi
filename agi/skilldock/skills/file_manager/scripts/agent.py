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
            description="Read, write, list, delete, move and search files in the workspace. Provides full filesystem management capabilities.",
            version="1.1.0",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string", 
                        "enum": ["read_file", "write_file", "list_directory", "delete_file", "move_file", "search_files", "get_file_info"],
                        "description": "Action to perform"
                    },
                    "path": {"type": "string", "description": "Primary path for the operation"},
                    "dest": {"type": "string", "description": "Destination path (for move_file)"},
                    "content": {"type": "string", "description": "Content to write (for write_file)"},
                    "pattern": {"type": "string", "description": "Glob pattern for search (e.g. *.py)"},
                    "recursive": {"type": "boolean", "default": False, "description": "Recursive list/search"}
                },
                "required": ["action"]
            },
            output_schema={
                "success": "bool",
                "content": "str",
                "data": "any",
                "message": "str"
            },
            category="io",
            sub_category="filesystem",
            tests=[
                SkillTestCase(
                    description="Write and Read File",
                    input={
                        "action": "write_file", 
                        "path": "test_file.txt", 
                        "content": "Hello World"
                    },
                    assertions=["Result success is True"]
                )
            ]
        )
    
    async def execute(self, action: str = None, path: str = None, **kwargs) -> Dict[str, Any]:
        """
        Execute file operation with enhanced capabilities.
        """
        # 1. Flexible Input Extraction & Aliasing
        action = action or kwargs.get("operation")
        path = path or kwargs.get("file_name") or kwargs.get("key") or kwargs.get("filename") or kwargs.get("file_path") or kwargs.get("source")
        dest = kwargs.get("dest") or kwargs.get("destination") or kwargs.get("target")
        content = kwargs.get("content") or ""
        pattern = kwargs.get("pattern") or "*"
        recursive = kwargs.get("recursive", False)

        if not action:
             return {"success": False, "message": "Missing 'action'"}

        # Normalize actions
        action = action.lower().replace(" ", "_")
        action_map = {
            "write": "write_file", "read": "read_file", "list": "list_directory",
            "delete": "delete_file", "remove": "delete_file", "move": "move_file",
            "rename": "move_file", "search": "search_files", "find": "search_files",
            "info": "get_file_info", "stats": "get_file_info"
        }
        action = action_map.get(action, action)

        if not path and action != "search_files":
             return {"success": False, "message": f"Path is required for action: {action}"}

        # 2. Safety Check (Basic)
        if path and ".." in os.path.normpath(path) and not path.startswith("/"):
             # Prevent escaping workspace if relative
             if os.path.normpath(path).startswith(".."):
                 return {"success": False, "message": "Access denied: Path outside workspace"}

        try:
            if action == "read_file":
                if not os.path.exists(path):
                    return {"success": False, "message": f"File not found: {path}"}
                
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
                return {"success": True, "data": data, "content": data, "message": f"Read {len(data)} chars"}
            
            elif action == "write_file":
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "message": f"Written to {path}"}
            
            elif action == "list_directory":
                if not os.path.exists(path):
                     return {"success": False, "message": f"Directory not found: {path}"}
                
                if recursive:
                    results = []
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            results.append(os.path.join(root, f))
                    return {"success": True, "data": results}
                else:
                    return {"success": True, "data": os.listdir(path)}

            elif action == "delete_file":
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                    return {"success": True, "message": f"Deleted directory: {path}"}
                else:
                    os.remove(path)
                    return {"success": True, "message": f"Deleted file: {path}"}

            elif action == "move_file":
                if not dest: return {"success": False, "message": "Destination 'dest' required"}
                import shutil
                shutil.move(path, dest)
                return {"success": True, "message": f"Moved {path} to {dest}"}

            elif action == "search_files":
                import glob
                search_root = path or "."
                p = os.path.join(search_root, "**", pattern) if recursive else os.path.join(search_root, pattern)
                files = glob.glob(p, recursive=recursive)
                return {"success": True, "data": files}

            elif action == "get_file_info":
                if not os.path.exists(path): return {"success": False, "message": "Path not found"}
                stats = os.stat(path)
                import time
                return {
                    "success": True,
                    "data": {
                        "size": stats.st_size,
                        "created": time.ctime(stats.st_ctime),
                        "modified": time.ctime(stats.st_mtime),
                        "is_dir": os.path.isdir(path)
                    }
                }
            
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
