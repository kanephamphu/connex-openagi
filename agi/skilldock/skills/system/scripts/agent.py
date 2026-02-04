
import subprocess
from typing import Any, Dict, List
from agi.skilldock.base import Skill, SkillMetadata

class SystemControlSkill(Skill):
    """
    Skill for controlling the macOS system (apps, volume, etc.).
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="system_control",
            description="Controls macOS system functions (open apps, set volume).",
            category="tool",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["open_app", "set_volume"], "description": "Action to perform"},
                    "app_name": {"type": "string", "description": "Name of app to open"},
                    "volume_level": {"type": "integer", "description": "Volume 0-100"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"}
                }
            }
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        
        if action == "open_app":
            return await self._open_app(kwargs.get("app_name"))
        elif action == "set_volume":
            return await self._set_volume(kwargs.get("volume_level"))
        else:
            return {"error": f"Unknown action: {action}"}

    async def _open_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"error": "App name required"}
            
        try:
            # osascript is safer than straight 'open' sometimes for activation
            # but 'open -a' is standard
            cmd = ["open", "-a", app_name]
            subprocess.run(cmd, check=True)
            return {"status": "success", "message": f"Opened {app_name}"}
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to open app: {e}"}

    async def _set_volume(self, level: int) -> Dict[str, Any]:
        if level is None:
            return {"error": "Volume level required"}
            
        try:
            # Map 0-100 to 0-7 (approx mac volume range is 0-7 or 0-100 depending on script)
            # set volume output volume X (0-100)
            script = f"set volume output volume {level}"
            subprocess.run(["osascript", "-e", script], check=True)
            return {"status": "success", "message": f"Set volume to {level}"}
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to set volume: {e}"}
