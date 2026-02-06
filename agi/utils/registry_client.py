"""
Shared utilities for interacting with the Connex Registry.
"""

import os
import json
import httpx
import importlib.util
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

class RegistryClient:
    """
    Common client for searching and downloading components from the registry.
    """
    
    def __init__(self, config):
        self.config = config
        
    async def search(self, component_type: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for components in the registry.
        """
        url = f"{self.config.registry_url}/{component_type}s/search"
        try:
             async with httpx.AsyncClient() as client:
                response = await client.get(url, params={"q": query, "page_size": limit}, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                return []
        except Exception as e:
            if self.config.verbose:
                print(f"[RegistryClient] Search failed for {component_type}: {e}")
            return []

    async def get_component(self, component_type: str, scoped_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full component data from registry.
        """
        url = f"{self.config.registry_url}/{component_type}s/{scoped_name}"
        headers = {}
        if self.config.connex_auth_token:
            headers["Authorization"] = f"Bearer {self.config.connex_auth_token}"
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=20)
                if response.status_code == 200:
                    return response.json()
            return None
        except Exception as e:
            if self.config.verbose:
                print(f"[RegistryClient] Failed to fetch {scoped_name}: {e}")
            return None

    async def download_and_save(self, component_type: str, scoped_name: str, storage_path: str) -> Optional[str]:
        """
        Download a component and save it to the local storage path.
        Returns the directory path where it was saved.
        """
        data = await self.get_component(component_type, scoped_name)
        if not data:
            return None
            
        # Sanitization
        safe_name = scoped_name.replace("@", "").replace("/", "_")
        install_dir = os.path.join(storage_path, safe_name)
        os.makedirs(install_dir, exist_ok=True)
        
        # Write Main code
        # Registry should provide 'implementationCode' or similar
        code = data.get("implementationCode") or data.get("implementation_code")
        if not code:
            if self.config.verbose:
                print(f"[RegistryClient] No implementation code for {scoped_name}")
            return None
            
        main_file = data.get("main", "agent.py")
        # Ensure main_file is just a filename
        main_file = os.path.basename(main_file)
        
        with open(os.path.join(install_dir, main_file), "w", encoding="utf-8") as f:
            f.write(code)
            
        # Write Manifest
        with open(os.path.join(install_dir, "connex.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # Extra files
        files = data.get("files", {})
        for fname, content in files.items():
            if ".." in fname or fname.startswith("/"):
                continue
            file_path = os.path.join(install_dir, fname)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        return install_dir
