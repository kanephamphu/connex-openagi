"""
Custom skill creation example.

Shows how to create and register your own skills with the AGI system.
"""

import asyncio
from typing import Dict, Any

from agi import AGI
from agi.skilldock.base import Skill, SkillMetadata


class BrandAnalysisSkill(Skill):
    """
    Custom skill for analyzing brand presence.
    
    This is an example of how you would create a specialized skill
    for your specific domain.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="brand_analyzer",
            description="Analyze brand presence and sentiment",
            input_schema={
                "brand_name": "str",
                "platforms": "List[str]"
            },
            output_schema={
                "sentiment_score": "float",
                "mentions": "int",
                "insights": "str"
            },
            category="marketing",
            timeout=45
        )
    
    async def execute(self, brand_name: str, platforms: list) -> Dict[str, Any]:
        """
        Analyze brand across platforms.
        
        In a real implementation, this would:
        - Query social media APIs
        - Analyze sentiment
        - Aggregate metrics
        """
        await self.validate_inputs(brand_name=brand_name, platforms=platforms)
        
        # Mock implementation
        print(f"  [BrandAnalyzer] Analyzing '{brand_name}' on {platforms}")
        
        # Simulate analysis
        await asyncio.sleep(1)
        
        return {
            "sentiment_score": 0.78,
            "mentions": 1247,
            "insights": f"{brand_name} has strong positive sentiment across {len(platforms)} platforms",
            "platforms_analyzed": platforms
        }


class CompetitorComparisonSkill(Skill):
    """Custom skill for comparing competitors."""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="competitor_comparison",
            description="Compare features and pricing of competitors",
            input_schema={
                "competitors": "List[str]",
                "focus_areas": "List[str]"
            },
            output_schema={
                "comparison": "dict",
                "winner": "str",
                "recommendations": "List[str]"
            },
            category="marketing"
        )
    
    async def execute(self, competitors: list, focus_areas: list) -> Dict[str, Any]:
        """Compare competitors."""
        await self.validate_inputs(competitors=competitors, focus_areas=focus_areas)
        
        print(f"  [CompetitorComparison] Comparing {len(competitors)} competitors")
        
        await asyncio.sleep(1)
        
        return {
            "comparison": {
                comp: {area: f"Rating: {8.5 - i*0.3}" for area in focus_areas}
                for i, comp in enumerate(competitors)
            },
            "winner": competitors[0] if competitors else "None",
            "recommendations": [
                "Focus on pricing competitiveness",
                "Enhance mobile features",
                "Improve customer support"
            ]
        }


async def main():
    """Demonstrate custom skill usage."""
    
    print("=" * 70)
    print("Custom Skill Example")
    print("=" * 70)
    
    # Initialize AGI
    agi = AGI()
    
    # Register custom skills
    print("\n📦 Registering custom skills...")
    agi.skill_registry.register(BrandAnalysisSkill())
    agi.skill_registry.register(CompetitorComparisonSkill())
    
    # List all available skills
    print("\n📋 Available skills:")
    for skill_meta in agi.skill_registry.list_skills():
        print(f"  • {skill_meta.name} ({skill_meta.category})")
        print(f"    {skill_meta.description}")
    
    # Now the planner can use these custom skills
    print("\n\n🚀 Executing goal with custom skills...")
    
    result = await agi.execute(
        goal="Analyze Govairo's brand and compare it with top 3 competitors",
        context={
            "brand": "Govairo",
            "competitors": ["HubSpot", "Marketo", "ActiveCampaign"],
            "platforms": ["Twitter", "LinkedIn", "Facebook"]
        }
    )
    
    print(f"\n✓ Execution complete")
    print(f"\nActions used:")
    for action in result['plan']['actions']:
        print(f"  • {action['skill']}: {action['description']}")
    
    print(f"\nFinal result: {result['result']}")


if __name__ == "__main__":
    asyncio.run(main())
