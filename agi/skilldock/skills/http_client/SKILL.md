---
name: http_client
description: HTTP Client for making network requests
category: web
sub_category: api
inputs:
  url:
    type: string
    description: Target URL
  method:
    type: string
    description: "HTTP method: 'GET' or 'POST'"
    required: false
  data:
    type: dict
    description: "JSON data for POST requests"
    required: false
outputs:
  content:
    type: string
    description: Response body
  status:
    type: integer
    description: HTTP status code
---

# HTTP Client Skills

## Instructions
Use `http_get` to fetch content from URLs.
Use `http_post` to send data to APIs.

## Examples
User: "Fetch google.com"
Assistant: Use `http_get` with `{"url": "https://google.com"}`
