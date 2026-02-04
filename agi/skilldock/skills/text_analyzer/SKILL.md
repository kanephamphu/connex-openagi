---
name: text_analyzer
description: Analyze text using LLMs
category: logic
sub_category: nlp
inputs:
  text:
    type: string
    description: The text content to analyze
  task:
    type: string
    description: "Analysis task: 'summarize', 'key_points', 'sentiment', 'translate'"
outputs:
  analysis:
    type: string
    description: The result of the analysis
---

# Text Analyzer Skill

## Instructions
Use `text_analyzer` (mock) or `llm_text_analyzer` (real) to process text.
Supported tasks: summarization, key point extraction, sentiment analysis, etc.

## Examples
User: "Summarize this article"
Assistant: Use `text_analyzer` with `{"text": "...", "task": "summarize"}`
