"""
Code execution skill for running Python code safely.
"""

import asyncio
import sys
from io import StringIO
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class CodeExecutorSkill(Skill):
    """
    Executes Python code in a controlled environment.
    
    WARNING: This is a simplified implementation. For production,
    use proper sandboxing (Docker, VM, or cloud functions).
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="code_executor",
            description="Execute Python code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Execution timeout in seconds", "default": 30}
                },
                "required": ["code"]
            },
            output_schema={
                "result": "Any",
                "stdout": "str",
                "stderr": "str"
            },
            category="execution",
            timeout=60,
            tests=[
                SkillTestCase(
                    description="Basic calculation",
                    input={"code": "print(2 + 2)"},
                    expected_output=None, # Stdout check is hard with exact match
                    assertions=["Stdout contains '4'"]
                ),
                SkillTestCase(
                    description="Variable return",
                    input={"code": "result = 'hello world'"},
                    expected_output={"result": "hello world", "success": True}
                )
            ]
        )
    
    async def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code.
        """
        await self.validate_inputs(code=code, timeout=timeout)
        
        # Capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        # Create isolated namespace
        namespace = {
            "__builtins__": __builtins__,
            "print": lambda *args, **kwargs: print(*args, **kwargs, file=stdout_capture)
        }
        
        result = None
        error = None
        
        try:
            # Execute code
            exec(code, namespace)
            
            # Try to get 'result' variable if defined
            if "result" in namespace:
                result = namespace["result"]
        
        except Exception as e:
            error = str(e)
            stderr_capture.write(f"Error: {e}\n")
        
        return {
            "result": result,
            "stdout": stdout_capture.getvalue().strip(),
            "stderr": stderr_capture.getvalue().strip(),
            "success": error is None,
            "error": error
        }


class SafeCodeExecutorSkill(Skill):
    """
    A safer code executor that runs code in a subprocess.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="safe_code_executor",
            description="Execute Python code in subprocess",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Execution timeout in seconds", "default": 30}
                },
                "required": ["code"]
            },
            output_schema={
                "result": "str",
                "stdout": "str",
                "stderr": "str"
            },
            category="execution",
            tests=[
                SkillTestCase(
                    description="Subprocess print",
                    input={"code": "print('subprocess test')"},
                    assertions=["Result contains 'subprocess test'"]
                )
            ]
        )
    
    async def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute code in subprocess."""
        await self.validate_inputs(code=code, timeout=timeout)
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode bytes
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            
            return {
                "result": stdout_str, # In subprocess, result is usually stdout
                "stdout": stdout_str,
                "stderr": stderr_str,
                "success": process.returncode == 0
            }
        
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return {
                "result": None,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "success": False
            }
