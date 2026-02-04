from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata
from agi.llm import LLMService

class LLMTextAnalyzer(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="llm_text_analyzer",
            description="Analyzes text using a large language model to extract insights and summaries.",
            version="1.0.0",
            inputs={"text": "The text to be analyzed."},
            outputs={"summary": "A summary of the text.", "insights": "Key insights extracted from the text."}
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        text = kwargs.get("text", "")
        if not text:
            raise ValueError("Input text is required for analysis.")

        llm_service = LLMService()
        summary = await llm_service.summarize(text)
        insights = await llm_service.extract_insights(text)

        return {
            "summary": summary,
            "insights": insights
        }