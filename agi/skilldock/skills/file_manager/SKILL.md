---
name: file_manager
description: Read, write, and manage files in the workspace
inputs:
  action:
    type: string
    description: "Supported: 'read_file', 'write_file', 'list_directory', 'delete_file'"
  path:
    type: string
    description: Target file or folder path
  content:
    type: string
    description: Content for write operations
    required: false
outputs:
  result:
    type: string
    description: File content or status message
---

# File Manager Skill

## Instructions
Use this skill to interact with the local filesystem.
Supported operations:
- `read_file`: Read content of a text file.
- `write_file`: Create or overwrite a text file.
- `list_directory`: List contents of a folder.

## Examples
User: "Read config.json"
Assistant: Use `file_manager` with `{"operation": "read_file", "path": "config.json"}`

User: "List files in the logs folder"
Assistant: Use `file_manager` with `{"operation": "list_directory", "path": "logs/"}`
