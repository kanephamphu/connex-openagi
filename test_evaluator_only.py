"""
Isolated test for the Evaluator.
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agi.config import AGIConfig
from agi.brain import GenAIBrain
from agi.motivation.evaluator import Evaluator

async def test_evaluator():
    print("\n[Test] Testing Evaluator only...\n")
    
    config = AGIConfig.from_env()
    brain = GenAIBrain(config)
    evaluator = Evaluator(brain)
    
    goal = "I need to analyze complex PDF documents which current tools fail at."
    actions = [
        {"id": "action_1", "status": "failed", "error": "Rate limit exceeded or skill missing capability for deep PDF analysis"}
    ]
    
    print(f"Goal: {goal}")
    print(f"Actions: {actions}")
    
    print("\nEvaluating...")
    evaluation = await evaluator.evaluate_performance(goal, actions)
    
    print("\nEvaluation Result:")
    import json
    print(json.dumps(evaluation, indent=2))

if __name__ == "__main__":
    asyncio.run(test_evaluator())
