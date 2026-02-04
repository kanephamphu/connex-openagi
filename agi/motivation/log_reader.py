"""
Log Reader for the Motivation System.

Parses AGI execution logs to extract traces for evaluation.
"""

import os
import re
from typing import List, Dict, Any, Optional

class LogReader:
    """
    Reads and parses AGI log files.
    """
    
    def __init__(self, log_path: str):
        self.log_path = log_path
        
    def read_recent_trace(self, max_lines: int = 500) -> str:
        """
        Reads the most recent lines from the log file.
        """
        if not os.path.exists(self.log_path):
            return ""
            
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                # Seek to end and read backwards if file is large, 
                # or just read tail for simplicity in this version.
                lines = f.readlines()
                return "".join(lines[-max_lines:])
        except Exception as e:
            print(f"[LogReader] Error reading log: {e}")
            return ""

    def extract_actions(self, log_content: str) -> List[Dict[str, Any]]:
        """
        Extracts action results and failures from the log content.
        
        Searches for patterns like "[Orchestrator] Executing action_..." 
        and "[Test] Result: ..." or "[Test] Action Failed: ...".
        """
        actions = []
        # Basic regex to find action execution and results in the specific log format seen
        action_blocks = re.split(r"\[Orchestrator\] Executing ", log_content)
        
        for block in action_blocks[1:]:  # Skip the part before the first action
            lines = block.split('\n')
            action_id_match = re.match(r"(action_\d+)", lines[0])
            if not action_id_match:
                continue
                
            action_id = action_id_match.group(1)
            action_data = {"id": action_id, "status": "unknown"}
            
            # Look for success/failure in the subsequent lines of the block
            for line in lines:
                if "Action Failed:" in line:
                    action_data["status"] = "failed"
                    action_data["error"] = line.split("Action Failed:")[1].strip()
                elif "Result:" in line:
                    action_data["status"] = "completed"
                    # Capture a snippet of the result
                    action_data["output_snippet"] = line.split("Result:")[1].strip()[:200]
                    
            actions.append(action_data)
            
        return actions
