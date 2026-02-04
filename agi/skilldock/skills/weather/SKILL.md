---
name: weather
description: Get real-time weather information for a location
category: web
sub_category: data
inputs:
  location:
    type: string
    description: City and country (e.g., "Hanoi, Vietnam" or "Paris, France")
outputs:
  forecast:
    type: string
    description: Weather forecast summary
  temperature:
    type: string
    description: Current temperature
---

# Weather Skill

## Instructions
Use this skill when the user asks about current weather or forecasts for a specific city.
If the location is missing, ask the user for it.
