---
name: web_search
description: Search the web for information
category: web
sub_category: search
inputs:
  query:
    type: string
    description: The search query
outputs:
  results:
    type: array
    description: List of search results
---

# Web Search Skill

## Instructions
Use this skill to search the internet for information when the user asks a question that requires external knowledge or recent events.

## Examples
User: "Who won the super bowl?"
Assistant: Use `web_search` with `{"query": "super bowl winner"}`
