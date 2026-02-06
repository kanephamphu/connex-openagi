try:
    import sys
    import os
    import torch
    print("Torch Imported")
    from agi.world.metaphysical.state import WorldState, Resource
    print("AGI State Imported")
    from agi.world.metaphysical.action import Action
    print("AGI Action Imported")
    from agi.world.metaphysical.causality_engine import CausalityEngine, ConservationGuard, StateVectorizer, ActionVectorizer
    print("AGI Engine Imported")
    print("All Imports OK")
except Exception as e:
    import traceback
    with open("import_error.log", "w") as f:
        f.write(str(e))
        f.write("\n")
        f.write(traceback.format_exc())
    print(f"Import Error: {e}")
