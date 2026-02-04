
import pyperclip
import asyncio
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class ClipboardPerception(PerceptionModule):
    """
    Senses changes in the system clipboard.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="clipboard_monitor",
            description="Monitors system clipboard for new content.",
            version="1.0.0"
        )
        
    def __init__(self, config):
        super().__init__(config)
        self.last_content = ""
        self.running = False

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Active check: Returns current content.
        """
        try:
            content = pyperclip.paste()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}

    # Ideally we'd have a 'start_loop' method in base.py for Active Perception
    # For now, we'll assume the external demo loop calls perceive(),
    # OR we simulate an event stream if the architecture supported it better.
    # The 'ReflexLayer' processes events. Who emits them?
    # Usually the 'PerceptionLayer' manages background tasks.
    # We will implement a 'check_for_changes' method that returns an event or None.
    
    async def check_change(self) -> Optional[Dict[str, Any]]:
        try:
            content = pyperclip.paste()
            if content != self.last_content:
                self.last_content = content
                if content: # Only report non-empty
                    return {
                        "type": "clipboard_change",
                        "payload": {"content": content}
                    }
        except:
            pass
        return None
