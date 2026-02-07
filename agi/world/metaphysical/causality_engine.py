"""
Latent Causality Engine: PyTorch-based Neural World Model.
Supports training, persistence, and deterministic guards.
"""

import json
import os
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError:
    # Dummy mocks to prevent import errors if torch is missing
    class MockAny:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return MockAny()
        def __getattr__(self, name): return MockAny()

    class MockTorch(MockAny):
        def __getattr__(self, name): return MockAny()
        class Tensor(MockAny): pass
        
    class MockNN(MockAny):
        class Module(MockAny): pass
        class Sequential(MockAny): pass
        class Linear(MockAny): pass
        class ReLU(MockAny): pass
        class MSELoss(MockAny): pass
        
    class MockOptim(MockAny):
        class Adam(MockAny): pass
        
    torch = MockTorch()
    nn = MockNN()
    optim = MockOptim()

from typing import List, Optional, Tuple, Dict, Any
from agi.world.metaphysical.state import WorldState, Resource, Entity
from agi.world.metaphysical.action import Action

class StateVectorizer:
    """Converts objective WorldState into a numerical tensor."""
    RESOURCE_MAP = {"storage": 0, "api_credits": 1, "time": 2, "health": 3, "egress": 4, "energy": 5}
    DIM = 6

    @staticmethod
    def vectorize(state: WorldState) -> torch.Tensor:
        vec = torch.zeros(StateVectorizer.DIM)
        for name, idx in StateVectorizer.RESOURCE_MAP.items():
            res = state.get_resource(name)
            if res:
                vec[idx] = float(res.value)
        return vec

    @staticmethod
    def devectorize(vec: torch.Tensor, original: WorldState) -> Dict[str, Any]:
        result = {"resources": {}}
        vec_list = vec.tolist()
        for name, idx in StateVectorizer.RESOURCE_MAP.items():
            result["resources"][name] = {"value": vec_list[idx]}
        return result

class ActionVectorizer:
    """Converts Action into a numerical tensor."""
    TYPE_MAP = {"CREATE_FILE": 0, "API_CALL": 1, "DELETE_FILE": 2, "SEND_DATA": 3}
    DIM = 10

    @staticmethod
    def vectorize(action: Action) -> torch.Tensor:
        vec = torch.zeros(ActionVectorizer.DIM)
        type_idx = ActionVectorizer.TYPE_MAP.get(action.type, -1)
        if type_idx != -1:
            vec[type_idx] = 1.0
        
        params = action.params
        vec[3] = float(params.get("size", 0)) / 1000.0
        vec[4] = float(params.get("cost", 0))
        return vec

class LatentTransitionModel(nn.Module):
    """
    Neural Network (MLP) for world dynamics.
    Learns the delta: S' = S + MLP(S, A)
    """
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, out_dim)
        )

    def forward(self, s_vec: torch.Tensor, a_vec: torch.Tensor) -> torch.Tensor:
        x = torch.cat([s_vec, a_vec], dim=-1)
        delta = self.net(x)
        return s_vec + delta

class ConservationGuard:
    """Ensures world state remains valid after neural projection."""
    def validate(self, original: WorldState, proposal_data: Dict[str, Any]) -> Tuple[WorldState, Optional[str]]:
        try:
            new_state = original.copy()
            for res_name, res_data in proposal_data.get("resources", {}).items():
                if res_name in new_state.resources:
                    new_val = res_data.get("value", new_state.resources[res_name].value)
                    if new_val < 0:
                        return original, f"Conservation Violation: {res_name} fell to {new_val:.2f}"
                    new_state.resources[res_name].value = new_val
            return new_state, None
        except Exception as e:
            return original, f"Guard failure: {str(e)}"

class CausalityEngine:
    """Neural Transition Model with Training and Persistence."""
    def __init__(self, model_path: Optional[str] = None):
        # Default to models/world_model.pth relative to project root
        if model_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            models_dir = os.path.join(project_root, "models")
            os.makedirs(models_dir, exist_ok=True)
            self.model_path = os.path.join(models_dir, "world_model.pth")
        else:
            self.model_path = model_path
            
        self.in_dim = StateVectorizer.DIM + ActionVectorizer.DIM
        self.out_dim = StateVectorizer.DIM
        self.model = LatentTransitionModel(self.in_dim, self.out_dim)
        self.guard = ConservationGuard()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        if model_path and os.path.exists(model_path):
            self.load_weights(model_path)

    async def predict(self, state: WorldState, action: Action) -> Tuple[WorldState, Optional[str]]:
        self.model.eval()
        with torch.no_grad():
            try:
                s_vec = StateVectorizer.vectorize(state)
                a_vec = ActionVectorizer.vectorize(action)
                next_s_vec = self.model(s_vec, a_vec)
                proposal_data = StateVectorizer.devectorize(next_s_vec, state)
                return self.guard.validate(state, proposal_data)
            except Exception as e:
                return state, f"Causality prediction failed: {str(e)}"

    def train_step(self, state: WorldState, action: Action, result_state: WorldState) -> float:
        """Single optimization step from experience."""
        self.model.train()
        self.optimizer.zero_grad()
        
        s_vec = StateVectorizer.vectorize(state)
        a_vec = ActionVectorizer.vectorize(action)
        target_s_vec = StateVectorizer.vectorize(result_state)
        
        pred_s_vec = self.model(s_vec, a_vec)
        loss = self.criterion(pred_s_vec, target_s_vec)
        
        loss.backward()
        self.optimizer.step()
        return loss.item()

    def save_weights(self, path: Optional[str] = None):
        torch.save(self.model.state_dict(), path or self.model_path)

    def load_weights(self, path: str):
        self.model.load_state_dict(torch.load(path))
        self.model.eval()

    async def simulate(self, state: WorldState, action: Action) -> Tuple[bool, Optional[str]]:
        _, error = await self.predict(state, action)
        return (error is None, error)
