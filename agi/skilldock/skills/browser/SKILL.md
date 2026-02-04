---
name: browser
description: Navigate and interact with websites using Playwright
category: web
sub_category: navigation
inputs:
  url:
    type: string
    description: The URL to visit
  action:
    type: string
    description: "Optional action: 'navigate', 'click', 'type', 'extract_text', 'extract_links'"
    required: false
  selector:
    type: string
    description: CSS selector for targeted actions
    required: false
  text_to_type:
    type: string
    description: Text to input into a field
    required: false
outputs:
  content:
    type: string
    description: Extract result or status
  url:
    type: string
    description: Current browser URL
---
# Browser Interaction Skill

A skill that allows the AGI to navigate URLs, interact with web elements, and extract content using a real browser (Playwright).

## Capabilities
- Navigate to specific URLs
- Click, type, and scroll
- Extract page text and metadata
- Take screenshots (future)
- Optional visible browser mode
