
---
name: time_sense
description: Provides time awareness and tick events.
category: system
sub_category: context
---

# Time Perception

**Type**: Passive Sensor
**Description**: Provides temporal awareness, emitting events for ticks, alarms, and schedule checks.

## Signals
- `timestamp`: float (epoch)
- `readable`: string
- `tick_type`: string ("second", "minute", "hour")
