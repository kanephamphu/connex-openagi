
---
name: intent_drift
description: Detects if the user's current request diverges from the ongoing task sequence.
category: core
sub_category: cognition
---

# Intent Drift Perception

**Type**: Active Sensor
**Description**: Monitors if the user's current requests diverge significantly from the established goal or context.

## Signals
- `drift_score`: float (0.0 - 1.0)
- `status`: string ("aligned", "drifting")
