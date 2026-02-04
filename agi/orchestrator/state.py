"""
Execution state management for the orchestrator.

Tracks progress through the action plan and stores intermediate results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class StepResult:
    """Result from executing a single action."""
    
    action_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ExecutionState:
    """
    Maintains state during plan execution.
    
    Tracks completed steps, pending steps, and intermediate results.
    """
    
    # Execution tracking
    completed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    pending: List[str] = field(default_factory=list)
    
    # Results storage
    results: Dict[str, StepResult] = field(default_factory=dict)
    
    # Global state for passing data between actions
    global_state: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    def mark_completed(self, action_id: str, result: StepResult):
        """Mark an action as completed."""
        if action_id in self.pending:
            self.pending.remove(action_id)
        self.completed.append(action_id)
        self.results[action_id] = result
        
        # Store outputs in global state for reference by other actions
        for key, value in result.output.items():
            self.global_state[f"{action_id}.{key}"] = value
    
    def mark_failed(self, action_id: str, result: StepResult):
        """Mark an action as failed."""
        if action_id in self.pending:
            self.pending.remove(action_id)
        self.failed.append(action_id)
        self.results[action_id] = result
    
    def get_result(self, action_id: str) -> Optional[StepResult]:
        """Get result for an action."""
        return self.results.get(action_id)
    
    def get_output(self, reference: str) -> Any:
        """
        Get output from a previous action using dot notation.
        
        Args:
            reference: Reference like "action_1.results" or "action_2.analysis"
            
        Returns:
            The referenced value
            
        Raises:
            KeyError: If reference doesn't exist
        """
        if reference in self.global_state:
            return self.global_state[reference]
        
        # Try direct lookup in results
        if "." in reference:
            action_id, key = reference.split(".", 1)
            if action_id in self.results:
                return self.results[action_id].output.get(key)
        
        raise KeyError(f"Reference not found: {reference}")
    
    def is_action_ready(self, action) -> bool:
        """
        Check if an action is ready to execute.
        
        An action is ready if all its dependencies are completed.
        
        Args:
            action: ActionNode to check
            
        Returns:
            True if ready to execute
        """
        for dep in action.depends_on:
            if dep not in self.completed:
                return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "completed": self.completed,
            "failed": self.failed,
            "pending": self.pending,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
