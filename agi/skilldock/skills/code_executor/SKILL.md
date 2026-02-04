---
name: code_executor
description: Execute Python code
inputs:
  code:
    type: string
    description: The Python code to execute
outputs:
  result:
    type: string
    description: The output of the code execution
  error:
    type: string
    description: Error message if execution failed
    required: false
---

# Code Executor Skill

## Instructions
Use this skill to execute Python code. This is useful for calculations, data processing, or any task that requires logic or computation.
Two variants are available: `code_executor` (in-process, risky) and `safe_code_executor` (subprocess).

## Examples
User: "Calculate the 10th Fibonacci number"
Assistant: Use `code_executor` with code to calculate it.
