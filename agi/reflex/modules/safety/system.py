
from typing import Any, Dict, List
from agi.reflex.base import ReflexModule, ReflexMetadata

class SafetyPolicyReflex(ReflexModule):
    """
    Automatic reflex that halts execution if forbidden content or high-risk goals are detected.
    """
    
    @property
    def metadata(self) -> ReflexMetadata:
        return ReflexMetadata(
            name="safety_policer",
            description="Enforces core safety and ethical boundaries instantly.",
            trigger_type="goal_analysis"
        )

    def __init__(self, config):
        super().__init__(config)
        self.forbidden_keywords = ["hack", "steal", "leak", "malware", "ddos", "destructive"]

    async def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Interprets the user goal or event payload for safety violations.
        """
        content = str(event.get("goal") or event.get("payload", "")).lower()
        
        # Immediate keyword intercept
        for word in self.forbidden_keywords:
            if word in content:
                print(f"[Reflex] SAFETY VIOLATION DETECTED: Found forbidden keyword '{word}'")
                return True
        return False
        
    async def get_plan(self) -> List[Dict[str, Any]]:
        """
        Returns a 'Denial' plan.
        """
        return [
            {
                "id": "safety_halt",
                "skill": "chat_response", # Assuming we have a chat_response or similar built-in
                "description": "Report safety violation to user",
                "inputs": {
                    "reply": "Reflex Error: This request violates safety policies. Execution halted at the nervous system layer."
                }
            }
        ]
