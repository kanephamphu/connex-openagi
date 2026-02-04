
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class ClipboardReflex(ReflexModule):
    """
    Acts on clipboard changes.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="smart_clipboard",
            description="Analyzes copied text and suggests actions.",
            trigger_type="clipboard_change"
        )
        
    def __init__(self, config):
        super().__init__(config)
        self.last_url = ""

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        if event.get("type") == "clipboard_change":
            content = event.get("payload", {}).get("content", "")
            # Simple heuristic: is it a URL?
            if content.startswith("http://") or content.startswith("https://"):
                self.last_url = content
                print(f"[Reflex] Smart Clipboard detected URL: {content[:30]}...")
                return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "offer_browsing",
                "skill": "speak",
                "description": "Offer to browse URL",
                "inputs": {
                    "text": f"I see you copied a link. Would you like me to read it?"
                }
            }
            # Enhanced version would insert a 'Browsing Task' into the Brain
        ]
