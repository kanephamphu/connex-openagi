---
name: memory
description: Store and recall information (Semantic Search)
category: core
sub_category: management
inputs:
  action:
    type: string
    description: "Supported actions: 'store', 'recall', 'list'"
  content:
    type: string
    description: "Specific content to store OR search query to recall"
outputs:
  result:
    type: string
    description: Search result or operation status
---

# Semantic Memory Skill ("The Soul")

## Instructions
Use this skill to store *meaningful* facts and recall them later using fuzzy matching.
Unlike a key-value store, you don't need to know the exact key.

Supported actions:
- `store`: Save information (e.g., "User likes hiking"). No key required, just `content`.
- `recall`: Search for information using a natural language query (e.g., "What are the user's hobbies?").
- `list`: Show recent memories.

## Examples
User: "My favorite color is green"
Assistant: Use `memory` with `{"action": "store", "content": "User favorite color is green"}`

User: "What should I get for my birthday? (Hint: color)"
Assistant: Use `memory` with `{"action": "recall", "content": "User preferences colors birthday"}`
