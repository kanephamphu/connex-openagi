
import subprocess
import os
import platform
import time
from typing import Any, Dict, List, Optional
from agi.skilldock.base import Skill, SkillMetadata

class SystemControlSkill(Skill):
    """
    Advanced Skill for controlling the macOS system (apps, volume, power, UI).
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="system_control",
            description="Controls macOS system functions: open/close apps, volume, brightness, screenshots, and system states (lock/sleep).",
            category="tool",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string", 
                        "enum": [
                            "open_app", "close_app", "set_volume", "set_brightness", 
                            "list_apps", "list_running", "screenshot", 
                            "lock", "sleep", "empty_trash",
                            "notification", "toggle_dark_mode", "get_battery",
                            "media_control", "minimize_all", "open_url"
                        ], 
                        "description": "Action to perform"
                    },
                    "app_name": {"type": "string", "description": "Name of app to open or close"},
                    "url": {"type": "string", "description": "URL to open (for open_url action)"},
                    "level": {"type": "integer", "description": "Level for volume or brightness (0-100)"},
                    "path": {"type": "string", "description": "Path to save screenshot (optional)"},
                    "text": {"type": "string", "description": "Text for notification"},
                    "title": {"type": "string", "description": "Title for notification"},
                    "media_action": {"type": "string", "enum": ["play", "pause", "next", "previous"], "description": "Media command"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "data": {"type": "any"}
                }
            }
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        
        if platform.system() != "Darwin":
            return {"error": "SystemControl skill currently only supports macOS (Darwin)."}

        if action == "open_app":
            return await self._open_app(kwargs.get("app_name"))
        elif action == "close_app":
            return await self._close_app(kwargs.get("app_name"))
        elif action == "set_volume":
            return await self._set_volume(kwargs.get("level"))
        elif action == "set_brightness":
            return await self._set_brightness(kwargs.get("level"))
        elif action == "list_apps":
            return await self._list_apps()
        elif action == "list_running":
            return await self._list_running()
        elif action == "screenshot":
            return await self._screenshot(kwargs.get("path"))
        elif action == "lock":
            # 'lock screen' is often invalid or restricted; using the native Lock Screen shortcut (Cmd+Ctrl+Q)
            return await self._run_osascript('tell application "System Events" to key code 12 using {control down, command down}')
        elif action == "sleep":
            return await self._run_osascript('tell application "System Events" to sleep')
        elif action == "empty_trash":
            return await self._run_osascript('tell application "Finder" to empty trash')
        elif action == "notification":
            return await self._notification(kwargs.get("text"), kwargs.get("title"))
        elif action == "toggle_dark_mode":
            return await self._toggle_dark_mode()
        elif action == "get_battery":
            return await self._get_battery()
        elif action == "media_control":
            return await self._media_control(kwargs.get("media_action"))
        elif action == "minimize_all":
            return await self._run_osascript('tell application "System Events" to set miniaturized of every window of (every process whose background only is false) to true')
        elif action == "open_url":
            url = kwargs.get("url")
            if not url: return {"error": "URL required"}
            try:
                subprocess.run(["open", url], check=True)
                return {"status": "success", "message": f"Opened URL: {url}"}
            except:
                return {"error": f"Failed to open URL: {url}"}
        else:
            return {"error": f"Unknown action: {action}"}

    async def _run_osascript(self, script: str) -> Dict[str, Any]:
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return {"status": "success", "message": "Command executed successfully"}
        except subprocess.CalledProcessError as e:
            return {"error": f"AppleScript failed: {e}"}

    async def _open_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"error": "App name required"}
        try:
            subprocess.run(["open", "-a", app_name], check=True)
            return {"status": "success", "message": f"Opened {app_name}"}
        except subprocess.CalledProcessError:
            return {"error": f"Could not find or open app: {app_name}"}

    async def _close_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"error": "App name required"}
        script = f'tell application "{app_name}" to quit'
        return await self._run_osascript(script)

    async def _set_volume(self, level: int) -> Dict[str, Any]:
        if level is None: return {"error": "Level required"}
        return await self._run_osascript(f"set volume output volume {max(0, min(100, level))}")

    async def _set_brightness(self, level: int) -> Dict[str, Any]:
        if level is None: return {"error": "Level required"}
        # Absolute brightness via AppleScript is restricted; using relative key codes for reliability.
        # Key code 107 is Brightness Down, 113 is Brightness Up.
        if level < 50:
            script = 'tell application "System Events" to repeat 4 times\nkey code 107\ndelay 0.1\nend repeat'
            msg = "Lowered brightness."
        else:
            script = 'tell application "System Events" to repeat 4 times\nkey code 113\ndelay 0.1\nend repeat'
            msg = "Raised brightness."
        
        res = await self._run_osascript(script)
        if "status" in res:
             res["message"] = msg
        return res

    async def _list_apps(self) -> Dict[str, Any]:
        try:
            apps = [f.replace(".app", "") for f in os.listdir("/Applications") if f.endswith(".app")]
            return {"status": "success", "data": sorted(apps)}
        except Exception as e:
            return {"error": f"Failed to list apps: {e}"}

    async def _list_running(self) -> Dict[str, Any]:
        script = 'tell application "System Events" to get name of every process whose background only is false'
        try:
            output = subprocess.check_output(["osascript", "-e", script]).decode().strip()
            running = [p.strip() for p in output.split(",")]
            return {"status": "success", "data": running}
        except:
            return {"error": "Failed to list running apps"}

    async def _screenshot(self, path: str = None) -> Dict[str, Any]:
        if not path:
            timestamp = int(time.time())
            path = os.path.expanduser(f"~/Desktop/screenshot_{timestamp}.png")
        try:
            subprocess.run(["screencapture", "-x", path], check=True)
            return {"status": "success", "message": f"Screenshot saved to {path}", "data": {"path": path}}
        except subprocess.CalledProcessError as e:
            return {"error": f"Screenshot failed: {e}"}

    async def _notification(self, text: str, title: str = None) -> Dict[str, Any]:
        if not text: return {"error": "Text required"}
        title_part = f'with title "{title}"' if title else ""
        script = f'display notification "{text}" {title_part}'
        return await self._run_osascript(script)

    async def _toggle_dark_mode(self) -> Dict[str, Any]:
        script = 'tell application "System Events" to tell appearance preferences to set dark mode to not dark mode'
        return await self._run_osascript(script)

    async def _get_battery(self) -> Dict[str, Any]:
        try:
            output = subprocess.check_output(["pmset", "-g", "batt"]).decode()
            # Parse: " -InternalBattery-0 (id=12345) 98%; discharging; 10:00 remaining"
            import re
            percent = re.search(r"(\d+)%", output)
            state = re.search(r";\s+([^;]+);", output)
            return {
                "status": "success", 
                "data": {
                    "raw": output.strip(),
                    "percentage": int(percent.group(1)) if percent else None,
                    "state": state.group(1) if state else "unknown"
                }
            }
        except:
            return {"error": "Failed to get battery info"}

    async def _media_control(self, action: str) -> Dict[str, Any]:
        if not action: return {"error": "Media action required"}
        cmds = {
            "play": "play",
            "pause": "pause",
            "next": "next track",
            "previous": "previous track"
        }
        # Try Music app primarily, then system events
        script = f'tell application "Music" to {cmds.get(action, "playpause")}'
        return await self._run_osascript(script)
