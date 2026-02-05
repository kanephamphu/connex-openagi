
import asyncio
import json
import os
import subprocess
import httpx
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
import concurrent.futures


class SubBrainHost:
    """
    Represents a dedicated host/service for a sub-brain (e.g., a local Ollama instance).
    """
    def __init__(self, config, host_id: int):
        self.config = config
        self.host_id = host_id
        self.url = config.sub_brain_url
        self.init_command = config.sub_brain_init_command
        self.health_endpoint = config.sub_brain_health_endpoint
        self.process: Optional[asyncio.subprocess.Process] = None
        self.client = AsyncOpenAI(
            api_key="local",
            base_url=self.url
        )

    async def is_healthy(self) -> bool:
        """Check if the sub-brain service is active and responding."""
        async with httpx.AsyncClient() as client:
            try:
                # Basic health check to the endpoint
                response = await client.get(self.health_endpoint, timeout=2.0)
                return response.status_code == 200
            except Exception:
                return False

    async def initialize(self) -> bool:
        """Ensure the host service is running and healthy."""
        if await self.is_healthy():
            print(f"[SubBrainHost-{self.host_id}] Service already healthy at {self.url}")
            return True

        print(f"[SubBrainHost-{self.host_id}] Starting service: {self.init_command}")
        try:
            self.process = await asyncio.create_subprocess_shell(
                self.init_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for health check with linear backoff
            for i in range(15): # wait up to 30 seconds
                await asyncio.sleep(2)
                if await self.is_healthy():
                    print(f"[SubBrainHost-{self.host_id}] Service healthy after {i*2}s.")
                    return True
            
            print(f"[SubBrainHost-{self.host_id}] Service failed to start or become healthy.")
            return False
        except Exception as e:
            print(f"[SubBrainHost-{self.host_id}] Error starting host: {e}")
            return False

    async def stop(self):
        """Terminate the host service if we started it."""
        if self.process:
            print(f"[SubBrainHost-{self.host_id}] Terminating process...")
            self.process.terminate()
            await self.process.wait()

    async def run_task(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Execute a simple task on the small local model."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.sub_brain_model,
                messages=messages,
                temperature=0.3,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"

class SubBrain:
    """
    A logical worker that uses a SubBrainHost.
    """
    def __init__(self, config, worker_id: int, host: SubBrainHost):
        self.config = config
        self.worker_id = worker_id
        self.host = host

    async def run_task(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return await self.host.run_task(prompt, system_prompt)

class SubBrainManager:
    """
    Manages a pool of sub-brains and their physical hosts.
    """
    def __init__(self, config):
        self.config = config
        # User requested "dedicated services", allowing for multiple hosts.
        # For now we default to one host, but infrastructure is ready for N hosts.
        self.hosts = [SubBrainHost(config, 0)] 
        self.sub_brains = [SubBrain(config, i, self.hosts[0]) for i in range(config.sub_brain_count)]
        
    async def initialize(self):
        """Initialize all hosts in parallel."""
        print(f"[SubBrainManager] Initializing {len(self.hosts)} sub-brain hosts...")
        results = await asyncio.gather(*[host.initialize() for host in self.hosts])
        return all(results)

    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute multiple tasks in parallel using available workers.
        """
        async def wrap_task(brain, task):
            return await brain.run_task(task["prompt"], task.get("system"))

        loop_tasks = []
        for i, task in enumerate(tasks):
            # Round-robin assignment across workers
            brain = self.sub_brains[i % len(self.sub_brains)]
            loop_tasks.append(wrap_task(brain, task))
            
        return await asyncio.gather(*loop_tasks)
