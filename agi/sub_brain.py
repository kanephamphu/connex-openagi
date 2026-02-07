
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
    def __init__(self, config, host_id: int, provider_override: Optional[str] = None, url_override: Optional[str] = None, model_override: Optional[str] = None):
        self.config = config
        self.host_id = host_id
        
        # 1. Resolve Provider
        # Priority: Override > Config > Default
        self.provider = provider_override
        if not self.provider:
            self.provider = getattr(config, 'sub_brain_provider', 'local')
            # Respect the global toggle if no override provided
            if self.config.use_external_subbrain and self.provider == 'local':
                 if self.config.openai_api_key:
                     self.provider = 'openai'
        
        # 2. Resolve URL
        self.url = url_override or config.sub_brain_url
        
        # 3. Resolve Model
        self.model = model_override or config.sub_brain_model
        
        # 4. Initialize Client
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=self.config.openai_api_key)
        elif self.provider == "groq":
            self.client = AsyncOpenAI(
                api_key=self.config.groq_api_key, 
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            # Default to local
            self.client = AsyncOpenAI(
                api_key="local",
                base_url=self.url
            )

    async def is_healthy(self) -> bool:
        """Check if the sub-brain service is active and responding."""
        if self.provider != "local":
            return True # Assume external SaaS is up
            
        async with httpx.AsyncClient() as client:
            try:
                # Basic health check to the endpoint
                response = await client.get(self.config.sub_brain_health_endpoint, timeout=2.0)
                return response.status_code == 200
            except Exception:
                return False

    async def initialize(self) -> bool:
        """Check if the host service is healthy."""
        if self.provider != "local":
             print(f"[SubBrainHost-{self.host_id}] configured for external provider: {self.provider}")
             return True
             
        is_up = await self.is_healthy()
        if is_up:
            print(f"[SubBrainHost-{self.host_id}] Service healthy at {self.url}")
            return True
        else:
            print(f"[SubBrainHost-{self.host_id}] ERR: Service not responding at {self.url}. Ensure it is running.")
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
            # Prepare arguments
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 1,
                "max_tokens": 256
            }
            
            # OpenAI o1/o3 series compatibility
            # Provide fail-over logic
            try:
                 response = await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                 err_str = str(e).lower()
                 retry = False
                 if "max_tokens" in err_str and "supported" in err_str:
                     kwargs.pop("max_tokens", None)
                     kwargs["max_completion_tokens"] = 256
                     retry = True
                 if "temperature" in err_str and "supported" in err_str:
                      # o1 often fixes temp to 1.0 or doesn't support it
                      kwargs["temperature"] = 1.0
                      retry = True
                      
                 if retry:
                     response = await self.client.chat.completions.create(**kwargs)
                 else:
                     raise e

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
        self.hosts: List[SubBrainHost] = []
        self.sub_brains: List[SubBrain] = []
        
        # 1. Configured Host (Primary)
        # This respects the user's main config (e.g. OpenAI w/ External enabled)
        primary_host = SubBrainHost(config, 0.0)
        self.hosts.append(primary_host)
        
        # 2. Secondary/Fallback Host
        # If primary is external, add a local fallback (if URL provided)
        # If primary is local, add an external fallback (OpenAI if Key provided)
        
        secondary_host = None
        if primary_host.provider != "local":
            # Primary is external, try adding local
            secondary_host = SubBrainHost(config, 1.0, 
                provider_override="local",
                url_override=config.sub_brain_url,
                model_override=config.sub_brain_model # Use configured local model name
            )
        elif config.openai_api_key:
            # Primary is local, try adding external
             secondary_host = SubBrainHost(config, 1.0, 
                 provider_override="openai", 
                 url_override=None
             )
        
        if secondary_host:
            self.hosts.append(secondary_host)
        
        # Create pool of workers
        # We assign workers to hosts in a balanced way, or just 1:1 for simplicity now
        for i in range(config.sub_brain_count):
            host = self.hosts[i % len(self.hosts)]
            self.sub_brains.append(SubBrain(config, i, host))
        
    async def initialize(self):
        """Initialize all hosts in parallel."""
        # Only init unique hosts
        unique_hosts = list(set(self.hosts))
        print(f"[SubBrainManager] Initializing {len(unique_hosts)} sub-brain hosts (Mix: {[h.provider for h in unique_hosts]})...")
        results = await asyncio.gather(*[host.initialize() for host in unique_hosts])
        return all(results)

    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute multiple tasks in parallel using available workers.
        
        Tasks can optionally specify 'provider' (local/external) to bias routing.
        """
        async def wrap_task(brain, task):
            return await brain.run_task(task["prompt"], task.get("system"))

        loop_tasks = []
        for i, task in enumerate(tasks):
            target_provider = task.get("provider")
            selected_brain = None
            
            # Simple routing logic
            if target_provider:
                for b in self.sub_brains:
                    # Match provider
                    if target_provider == "local" and b.host.provider == "local":
                        selected_brain = b
                        break
                    elif target_provider == "external" and b.host.provider != "local":
                        selected_brain = b
                        break
                    elif b.host.provider == target_provider:
                         selected_brain = b
                         break
            
            # Fallback to round-robin
            if not selected_brain:
                selected_brain = self.sub_brains[i % len(self.sub_brains)]
                
            loop_tasks.append(wrap_task(selected_brain, task))
            
        return await asyncio.gather(*loop_tasks)
