"""
World Trainer: Modular Concept-Based Training for the Neural World Model.
Loads experience tuples (S, A, S') from JSON dataset files.
"""

import sys
import os
import torch
import json
import glob
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from agi.world.metaphysical.state import WorldState, Resource
from agi.world.metaphysical.action import Action
from agi.world.metaphysical.causality_engine import CausalityEngine

def load_concept_datasets(datasets_dir: str) -> List[tuple]:
    """
    Reads all JSON files in the datasets directory and converts them to (S, A, S') tuples.
    """
    experience = []
    dataset_files = glob.glob(os.path.join(datasets_dir, "*.json"))
    
    print(f"Found {len(dataset_files)} concept dataset files.")
    
    for file_path in dataset_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for concept_group in data:
                concept_name = concept_group.get("concept", "unknown")
                samples = concept_group.get("samples", [])
                print(f"  - Loading concept '{concept_name}' ({len(samples)} samples) from {os.path.basename(file_path)}")
                
                for sample in samples:
                    # 1. State (S)
                    state_data = sample["state"]
                    s = WorldState()
                    for name, val in state_data.items():
                        s.resources[name] = Resource(name, val)
                    
                    # 2. Action (A)
                    action_data = sample["action"]
                    action = Action(agent="agi", type=action_data["type"], params=action_data.get("params", {}))
                    
                    # 3. Result State (S')
                    result_data = sample["result"]
                    s_prime = WorldState()
                    for name, val in result_data.items():
                        s_prime.resources[name] = Resource(name, val)
                    
                    experience.append((s, action, s_prime))
                    
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    return experience

def train_world_cognition(datasets_dir: str, epochs: int = 100):
    """Train the Neural World Model on concept-based experience."""
    engine = CausalityEngine()
    experience = load_concept_datasets(datasets_dir)
    
    if not experience:
        print("No experience samples found. Aborting training.")
        return
        
    print(f"\nStarting World Cognition training on {len(experience)} samples for {epochs} epochs...")
    
    for epoch in range(1, epochs + 1):
        total_loss = 0
        # Shuffle experience for better training
        random_indices = torch.randperm(len(experience)).tolist()
        
        for idx in random_indices:
            s, a, sp = experience[idx]
            loss = engine.train_step(s, a, sp)
            total_loss += loss
        
        if epoch == 1 or epoch % 20 == 0:
            avg_loss = total_loss / len(experience)
            print(f"Epoch {epoch:3d}/{epochs} | Avg Loss: {avg_loss:.8f}")
            
    engine.save_weights()
    print("\nTraining complete. Modular world cognition weights saved to world_model.pth")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Neural World Model on concept datasets.")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs.")
    parser.add_argument("--datasets", type=str, default=None, help="Path to datasets directory.")
    args = parser.parse_args()
    
    # Default datasets directory relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_path = args.datasets or os.path.join(current_dir, "..", "datasets")
    
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)
        print(f"Created datasets directory at {datasets_path}")
        
    train_world_cognition(datasets_path, epochs=args.epochs)
