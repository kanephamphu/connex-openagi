"""
Tier 3: The SkillDock (Workers)

Skill registry and execution layer.
"""

from agi.skilldock.registry import SkillRegistry
from agi.skilldock.base import Skill, SkillMetadata

__all__ = ["SkillRegistry", "Skill", "SkillMetadata"]
