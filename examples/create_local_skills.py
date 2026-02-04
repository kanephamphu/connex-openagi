"""
Script to generate local example skills using the SkillCreatorSkill.
"""

import asyncio
import os
from agi import AGI, AGIConfig
from agi.skilldock.skills.skill_creator import SkillCreatorSkill

# 1. Weather Skill
WEATHER_CODE = """
import random
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase

class WeatherSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="weather",
            description="Get weather information for a location",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                },
                "required": ["location"]
            },
            output_schema={"temperature": "float", "condition": "str"},
            category="information",
            tests=[
                SkillTestCase(
                    description="Get weather for London",
                    input={"location": "London"},
                    assertions=["Temperature is a number", "Condition is a string"]
                )
            ]
        )

    async def execute(self, location: str, unit: str = "celsius") -> Dict[str, Any]:
        # Mock weather
        conds = ["Sunny", "Rainy", "Cloudy", "Windy"]
        temp = random.randint(10, 30) if unit == "celsius" else random.randint(50, 85)
        return {
            "temperature": temp,
            "condition": random.choice(conds),
            "unit": unit,
            "location": location
        }
"""

WEATHER_INSTRUCT = """
Use this skill to retrieve current weather conditions for a specific city.
Defaults to Celsius.
"""

WEATHER_EXAMPLES = """
User: "What's the weather in Tokyo?"
Assistant: Use `weather` with `{"location": "Tokyo"}`

User: "How hot is it in Phoenix in F?"
Assistant: Use `weather` with `{"location": "Phoenix", "unit": "fahrenheit"}`
"""

# 2. Calculator Skill
CALC_CODE = """
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase

class CalculatorSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="calculator",
            description="Perform basic arithmetic operations",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression (e.g. '2 + 2')"}
                },
                "required": ["expression"]
            },
            output_schema={"result": "float"},
            category="utilities",
            tests=[
                SkillTestCase(
                    description="Addition",
                    input={"expression": "50 + 50"},
                    expected_output={"result": 100}
                )
            ]
        )

    async def execute(self, expression: str) -> Dict[str, Any]:
        # Safe eval
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            raise ValueError("Invalid characters in expression")
        return {"result": eval(expression)}
"""

CALC_INSTRUCT = """
Use for basic math operations (+, -, *, /).
"""

CALC_EXAMPLES = """
User: "Calculate 25 * 4"
Assistant: Use `calculator` with `{"expression": "25 * 4"}`
"""

async def main():
    print("="*60)
    print("Generating Local Example Skills")
    print("="*60)
    
    config = AGIConfig.from_env()
    # Force skills storage to project dir for visibility
    config.skills_storage_path = os.path.join(os.getcwd(), "installed_skills")
    os.makedirs(config.skills_storage_path, exist_ok=True)
    
    creator = SkillCreatorSkill(config)
    
    # Create Weather
    print("\n[Action] Creating @connex/weather...")
    res1 = await creator.execute(
        name="@connex/weather",
        code=WEATHER_CODE,
        description="Get weather information",
        instructions=WEATHER_INSTRUCT,
        examples=WEATHER_EXAMPLES,
        publish=False # Local install
    )
    print(f"[Result] {res1['message']}")
    
    # Create Calculator
    print("\n[Action] Creating @connex/calculator...")
    res2 = await creator.execute(
        name="@connex/calculator",
        code=CALC_CODE,
        description="Basic calculator",
        instructions=CALC_INSTRUCT,
        examples=CALC_EXAMPLES,
        publish=False
    )
    print(f"[Result] {res2['message']}")
    
    print(f"\nSkills generated in: {config.skills_storage_path}")

if __name__ == "__main__":
    asyncio.run(main())
