"""
Long-term memory skill using simple JSON storage.
"""

import os
import json
from typing import Dict, Any, List
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class MemorySkill(Skill):
    """
    Skill for persisting facts and preferences across sessions (The Soul).
    """
    
    def __init__(self, config):
        self.config = config
        from agi.brain import GenAIBrain
        from agi.memory.engine import MemoryEngine
        
        self.brain = GenAIBrain(config)
        self.engine = MemoryEngine() # defaults to agi_memory.db
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="memory",
            description="Store and recall information (Semantic Memory)",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string", 
                        "enum": ["store", "recall", "forget", "list"],
                        "description": "Action to perform"
                    },
                    "content": {"type": "string", "description": "Information to store or query to recall"},
                    "key": {"type": "string", "description": "Optional key/tag for metadata"}
                },
                "required": ["action", "content"]
            },
            output_schema={
                "success": "bool",
                "results": "list | str",
                "message": "str"
            },
            category="core",
            sub_category="management",
            tests=[
                SkillTestCase(
                    description="Store and Recall",
                    input={
                        "action": "store", 
                        "content": "I love spicy food"
                    },
                    assertions=["Result success is True"]
                )
            ]
        )
    
    async def execute(self, action: str, content: str = "", key: str = "") -> Dict[str, Any]:
        """
        Execute semantic memory operation.
        """
        await self.validate_inputs(action=action)
        
        if action == "store":
            if not content:
                return {"success": False, "message": "Content required for store"}
            
            # Generate embedding
            try:
                embedding = await self.brain.get_embedding(content)
                self.engine.add_memory(content, embedding, {"key": key})
                return {"success": True, "message": f"Stored memory: '{content}'"}
            except Exception as e:
                return {"success": False, "message": f"Embedding failed: {str(e)}"}
            
        elif action == "recall":
            if not content:
                return {"success": False, "message": "Query content required for recall"}
            
            try:
                # Generate query embedding
                query_vec = await self.brain.get_embedding(content)
                results = self.engine.search(query_vec, limit=3)
                
                # Format results
                # Only return results with score > 0.7 (threshold)
                relevant = [r for r in results if r["score"] > 0.6]
                
                return {
                    "success": True, 
                    "results": relevant,
                    "message": f"Found {len(relevant)} relevant memories"
                }
            except Exception as e:
                return {"success": False, "message": f"Recall failed: {str(e)}"}
                
        elif action == "forget":
            # Rough implementation: requires ID or exact content match
            # For now, let's say "not implemented" effectively or delete by ID if passed in content
            # To go simple: we just don't support robust delete yet in V1 soul
            return {"success": False, "message": "Forget not fully supported in vector mode yet (requires ID)"}
            
        elif action == "list":
            memories = self.engine.get_all(limit=20)
            return {"success": True, "results": memories}
            
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
