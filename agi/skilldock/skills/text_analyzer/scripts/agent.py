"""
Text analysis skill using LLMs.
"""

from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class TextAnalyzerSkill(Skill):
    """
    Analyzes and summarizes text using LLMs (Mock implementation).
    """
    
    def __init__(self, config=None):
        self.config = config
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="text_analyzer",
            description="Analyze and summarize text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "task": {"type": "string", "description": "Analysis task (e.g., summarize)", "default": "summarize"}
                },
                "required": ["text"]
            },
            output_schema={
                "analysis": "str"
            },
            category="logic",
            sub_category="nlp",
            timeout=60,
            tests=[
                SkillTestCase(
                    description="Summarize short text",
                    input={"text": "This is a long story about nothing.", "task": "summarize"},
                    assertions=["Analysis starts with 'Summary:'"]
                )
            ]
        )
    async def execute(self, text: Any, task: str = "summarize") -> Dict[str, Any]:
        """
        Analyze text according to task.
        """
        await self.validate_inputs(text=text, task=task)
        
        # Simple mock implementation
        if "summarize" in task.lower():
            analysis = f"Summary: {text[:50]}..."
        elif "extract" in task.lower() and "key" in task.lower():
            analysis = "Key points:\n1. Mock Point 1\n2. Mock Point 2"
        else:
            analysis = f"Analysis: Processed text with task '{task}'"
        
        return {"analysis": analysis}


class LLMTextAnalyzerSkill(Skill):
    """
    Text analyzer that uses actual LLM for analysis.
    """
    
    def __init__(self, config):
        self.config = config
        self.client = config.get_executor_client()
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="llm_text_analyzer",
            description="Analyze text using LLM",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "task": {"type": "string", "description": "Analysis task", "default": "summarize"}
                },
                "required": ["text"]
            },
            output_schema={
                "analysis": "str"
            },
            category="logic",
            sub_category="nlp",
            tests=[
                SkillTestCase(
                    description="Sentiment analysis",
                    input={"text": "I love this product!", "task": "sentiment analysis"},
                    assertions=["Result contains 'positive'"]
                )
            ]
        )
    async def execute(self, text: Any, task: str = "summarize") -> Dict[str, Any]:
        """Analyze text using LLM."""
        await self.validate_inputs(text=text, task=task)
        
        prompt = f"Task: {task}\n\nText:\n{text}\n\nProvide your analysis:"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.executor_model,
                messages=[
                    {"role": "system", "content": "You are a text analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
        except Exception as e:
            analysis = f"Error during LLM analysis: {str(e)}"
        
        return {"analysis": analysis}
