"""
Verification test for the Vectorized Neural World Layer 2.0 (No Prompts).
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
from agi.world.metaphysical.state import WorldState, Resource
from agi.world.metaphysical.action import Action
from agi.world.metaphysical.causality_engine import CausalityEngine, ConservationGuard, StateVectorizer, ActionVectorizer

# Redirect stdout to both file and console
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("test_verification_direct.log", "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()

def test_state_vectorization():
    """Verify WorldState -> Vector -> Proposal conversion."""
    print("\n--- Testing State Vectorization ---")
    state = WorldState()
    state.resources["storage"] = Resource("storage", 500)
    state.resources["api_credits"] = Resource("api_credits", 50)
    print(f"Input State: storage=500, api_credits=50")
    
    vec = StateVectorizer.vectorize(state)
    print(f"Vector Result: {vec}")
    assert vec[0] == 500.0
    assert vec[1] == 50.0
    
    proposal = StateVectorizer.devectorize(vec, state)
    print(f"Devectorized Proposal: {proposal}")
    assert proposal["resources"]["storage"]["value"] == 500.0
    print("Result: PASS")

def test_action_vectorization():
    """Verify Action -> Vector conversion."""
    print("\n--- Testing Action Vectorization ---")
    action = Action(agent="agi", type="API_CALL", params={"cost": 1.0})
    print(f"Input Action: {action.type}, params={action.params}")
    
    vec = ActionVectorizer.vectorize(action)
    print(f"Vector Result: {vec}")
    
    assert vec[1] == 1.0 # API_CALL position
    assert vec[4] == 1.0 # cost param position
    print("Result: PASS")

async def test_latent_neural_transition():
    """Verify that the latent MLP model predicts a state change."""
    print("\n--- Testing Latent Neural Transition ---")
    engine = CausalityEngine()
    state = WorldState()
    state.resources["storage"] = Resource("storage", 1000)
    
    action = Action(agent="agi", type="CREATE_FILE", params={"size": 100})
    print(f"Initial State: storage={state.get_resource('storage').value}")
    print(f"Action: {action.type}, size: 100")
    
    next_state, error = await engine.predict(state, action)
    
    print(f"Predicted State storage: {next_state.get_resource('storage').value}")
    assert error is None
    assert isinstance(next_state, WorldState)
    assert next_state.get_resource("storage").value != 1000.0
    print("Result: PASS")

def test_conservation_guard_negative_block():
    """Verify the guard still blocks negative resources in latent space."""
    print("\n--- Testing Conservation Guard Negative Block ---")
    guard = ConservationGuard()
    original = WorldState()
    original.resources["health"] = Resource("health", 10)
    
    proposal = {"resources": {"health": {"value": -5.0}}}
    print(f"Original Health: 10, Proposed Health: -5.0")
    
    _, error = guard.validate(original, proposal)
    print(f"Guard Error Result: {error}")
    assert "Conservation Violation" in error
    print("Result: PASS")

if __name__ == "__main__":
    import asyncio
    
    print("Running manual verification with self-logging...")
    try:
        test_state_vectorization()
        test_action_vectorization()
        asyncio.run(test_latent_neural_transition())
        test_conservation_guard_negative_block()
        print("\nAll verification tests completed successfully.")
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        sys.exit(1)
    finally:
        sys.stdout.log.close()
