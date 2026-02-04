---
name: file_manager
description: Read, write, and manage files in the workspace
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
