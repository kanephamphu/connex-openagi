---
name: general_chat
description: Handle general conversation, greetings, and non-technical questions
category: communication
sub_category: chat
inputs:
  message:
    type: string
    description: The user's message
  history:
    type: array
    description: Previous conversation history (optional)
    required: false
outputs:
  reply:
    type: string
    description: The AI's response
---

# General Chat Skill

## Instructions
Use this skill for conversational queries, greetings, or questions not requiring complex tools.
If the user asks "Hi", "How are you", or "Who are you?", use this skill.
Also use this for general knowledge questions like "Why is the sky blue?" if no web search is explicitly requested.

## Examples
User: "Hello"
Assistant: Use `general_chat` with `{"message": "Hello"}`

User: "Tell me a joke"
Assistant: Use `general_chat` with `{"message": "Tell me a joke"}`
