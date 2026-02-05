"""
History Manager for AGI executions.

Persists execution traces and provides access for UI/API.
"""
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

class HistoryManager:
    """Manages persistence of AGI execution history."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "agi_history.json"
        
    def _load(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            return json.loads(self.history_file.read_text(encoding="utf-8"))
        except:
            return []
            
    def _save(self, history: List[Dict[str, Any]]):
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
        
    def add_trace(self, goal: str, events: List[Dict[str, Any]]) -> str:
        """
        Save a new execution trace.
        Returns the ID of the new entry.
        """
        entry_id = str(uuid.uuid4())
        
        # Calculate status
        status = "unknown"
        if events:
            last = events[-1]
            if last.get("type") == "error":
                status = "failed"
            elif last.get("type") == "execution_completed":
                status = "success" if last.get("success") else "failed"
            elif last.get("type") == "action_completed" and last.get("action_id") == "chat_response":
                status = "success" # Chat intent
                
        entry = {
            "id": entry_id,
            "timestamp": time.time(),
            "goal": goal,
            "status": status,
            "events": events
        }
        
        history = self._load()
        history.insert(0, entry) # Prepend (newest first)
        
        # Limit to last 10 runs to keep file size sane and follow user request
        if len(history) > 10:
            history = history[:10]
            
        self._save(history)
        return entry_id
        
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summary of recent executions (without full trace events)."""
        history = self._load()
        # Return stripped version
        return [{k: v for k, v in item.items() if k != "events"} for item in history[:limit]]
        
    def get_trace(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get full trace for a specific execution."""
        history = self._load()
        for item in history:
            if item["id"] == entry_id:
                return item
        return None
