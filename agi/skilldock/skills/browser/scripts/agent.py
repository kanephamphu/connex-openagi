import os
import asyncio
from typing import Dict, Any, List, Optional
from agi.skilldock.base import Skill, SkillMetadata
from playwright.async_api import async_playwright


class BrowserSkill(Skill):
    """
    Interact with websites using a real browser.
    Supports navigation, clicking, typing, and content extraction.
    """

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="browser",
            description="Interact with websites using a real browser to search, research, and investigate. Supports navigation, clicking, typing, and content extraction.",
            category="web",
            version="1.0.0",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["navigate", "click", "type", "extract", "scroll"],
                        "description": "The action to perform"
                    },
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "selector": {"type": "string", "description": "CSS selector for click/type"},
                    "text": {"type": "string", "description": "Text to type"},
                    "wait_for": {"type": "string", "description": "Selector to wait for after navigation"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "url": {"type": "string"},
                    "content": {"type": "string"},
                    "title": {"type": "string"},
                    "error": {"type": "string"}
                }
            },
            config_schema={
                "type": "object",
                "properties": {
                    "HEADLESS": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to run browser in headless mode. Set to False to see the browser window."
                    },
                    "TIMEOUT": {
                        "type": "integer",
                        "default": 30000,
                        "description": "Browser timeout in milliseconds"
                    }
                }
            },
            requirements=["playwright"]
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        url = kwargs.get("url")
        selector = kwargs.get("selector")
        text = kwargs.get("text")
        wait_for = kwargs.get("wait_for")

        headless = self.config.get("HEADLESS", False)
        timeout = self.config.get("TIMEOUT", 30000)

        results = {"success": False}

        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=headless)
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(timeout)

                if action == "navigate" or url:
                    if not url:
                        return {"success": False, "error": "URL is required for navigation"}
                    await page.goto(url, wait_until="domcontentloaded")
                    if wait_for:
                        await page.wait_for_selector(wait_for)
                
                if action == "click":
                    if not selector:
                        return {"success": False, "error": "Selector is required for click"}
                    await page.wait_for_selector(selector)
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")

                if action == "type":
                    if not selector or text is None:
                        return {"success": False, "error": "Selector and text are required for type"}
                    await page.wait_for_selector(selector)
                    await page.fill(selector, text)

                if action == "scroll":
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)

                # Always extract content after action for context
                results["url"] = page.url
                results["title"] = await page.title()
                
                if action == "extract":
                    # Simple text extraction for now
                    results["content"] = await page.inner_text("body")
                
                results["success"] = True
                await browser.close()

        except Exception as e:
            results["error"] = str(e)
            results["success"] = False

        return results
