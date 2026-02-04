"""
HTTP client skill for fetching web content.
"""

import httpx
from typing import Dict, Any
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class HTTPGetSkill(Skill):
    """
    Fetches content from URLs via HTTP GET.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="http_get",
            description="Fetch content from a URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            },
            output_schema={
                "content": "str",
                "status_code": "int"
            },
            category="network",
            timeout=30,
            tests=[
                SkillTestCase(
                    description="Fetch Google",
                    input={"url": "https://www.google.com"},
                    assertions=["Status code is 200", "Content contains 'html'"]
                )
            ]
        )
    
    async def execute(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from URL.
        """
        await self.validate_inputs(url=url)
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=20.0)
                
                return {
                    "content": response.text,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "content": "",
                "status_code": 0,
                "error": str(e)
            }


class HTTPPostSkill(Skill):
    """
    Sends HTTP POST requests.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="http_post",
            description="Send HTTP POST request",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to POST to"},
                    "data": {"type": "object", "description": "JSON data payload"}
                },
                "required": ["url", "data"]
            },
            output_schema={
                "response": "str",
                "status_code": "int"
            },
            category="network",
            tests=[
                SkillTestCase(
                    description="Post to header echo (Mock)",
                    input={"url": "https://httpbin.org/post", "data": {"test": "value"}},
                    assertions=["Status code is 200"]
                )
            ]
        )
    
    async def execute(self, url: str, data: dict) -> Dict[str, Any]:
        """
        Send POST request.
        """
        await self.validate_inputs(url=url, data=data)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=20.0)
                
                return {
                    "response": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
             return {
                "response": "",
                "status_code": 0,
                "error": str(e)
            }
