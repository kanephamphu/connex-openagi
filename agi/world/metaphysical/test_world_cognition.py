"""
World Cognition Tester: Validates the trained Neural World Model against concept datasets.
Reports Mean Squared Error (MSE) and Mean Absolute Error (MAE) per concept.
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
from agi.world.metaphysical.causality_engine import CausalityEngine, StateVectorizer

def test_concept_datasets(datasets_dir: str):
    """Loads and tests the model against all concept JSON files."""
    engine = CausalityEngine()
    dataset_files = glob.glob(os.path.join(datasets_dir, "*.json"))
    
    if not dataset_files:
        print(f"[ERROR] No dataset files found in {datasets_dir}")
        return

    print("==========================================")
    print("AGI World Model: Cognition Validation Report")
    print("==========================================\n")

    overall_results = []

    for file_path in dataset_files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for concept_group in data:
                concept_name = concept_group.get("concept", "unknown")
                samples = concept_group.get("samples", [])
                
                print(f"Testing Concept: {concept_name} ({len(samples)} samples)")
                
                total_mse = 0.0
                total_mae = 0.0
                
                for sample in samples:
                    # 1. Setup S, A, S_target
                    s = WorldState()
                    for k, v in sample["state"].items(): s.resources[k] = Resource(k, v)
                    
                    action = Action(agent="agi", type=sample["action"]["type"], params=sample["action"].get("params", {}))
                    
                    s_target_vec = StateVectorizer.vectorize(
                        WorldState(resources={k: Resource(k, v) for k, v in sample["result"].items()})
                    )

                    # 2. Predict with Neural Model
                    engine.model.eval()
                    with torch.no_grad():
                        s_vec = StateVectorizer.vectorize(s)
                        a_vec = engine.ActionVectorizer.vectorize(action) if hasattr(engine, 'ActionVectorizer') else None
                        
                        # Use engine's internal predict logic but get vector for direct comparison
                        from agi.world.metaphysical.causality_engine import ActionVectorizer
                        a_vec = ActionVectorizer.vectorize(action)
                        
                        s_pred_vec = engine.model(s_vec, a_vec)
                        
                        # 3. Compute Metrics
                        mse = torch.mean((s_pred_vec - s_target_vec)**2).item()
                        mae = torch.mean(torch.abs(s_pred_vec - s_target_vec)).item()
                        
                        total_mse += mse
                        total_mae += mae
                
                avg_mse = total_mse / len(samples)
                avg_mae = total_mae / len(samples)
                
                status = "PASS (Cognition Accurate)" if avg_mae < 0.1 else "FAIL (Needs retraining)"
                print(f"  - Avg MSE: {avg_mse:.8f}")
                print(f"  - Avg MAE: {avg_mae:.8f}")
                print(f"  - Status:  {status}\n")
                
                overall_results.append({
                    "concept": concept_name,
                    "avg_mse": avg_mse,
                    "avg_mae": avg_mae,
                    "status": status
                })

        except Exception as e:
            print(f"[ERROR] Failed to test {file_name}: {e}\n")

    print("Summary:")
    for res in overall_results:
        print(f"  [{res['status'][:4]}] {res['concept']}: MSE={res['avg_mse']:.6f}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_path = os.path.join(current_dir, "..", "datasets")
    test_concept_datasets(datasets_path)
