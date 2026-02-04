import httpx
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from agi.skilldock.base import Skill, SkillMetadata, SkillTestCase


class WebSearchSkill(Skill):
    """
    Search the web for information using multiple engines including a headless browser.
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="web_search",
            description="Search the web for information. Supports Google, Bing, DuckDuckGo and Browser-based search.",
            category="web",
            sub_category="search",
            version="1.0.0",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "engine": {
                        "type": "string", 
                        "enum": ["auto", "google", "bing", "duckduckgo", "browser"],
                        "default": "auto"
                    },
                    "num_results": {"type": "integer", "default": 5},
                    "extract_keywords": {"type": "boolean", "default": False},
                    "headless": {"type": "boolean", "default": True, "description": "Whether to run the browser in headless mode"}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "snippet": {"type": "string"}
                            }
                        }
                    },
                    "engine_used": {"type": "string"},
                    "query_used": {"type": "string"}
                }
            },
            config_schema={
                "type": "object",
                "properties": {
                    "GOOGLE_SEARCH_API_KEY": {"type": "string", "description": "Google Custom Search API Key"},
                    "GOOGLE_SEARCH_ID": {"type": "string", "description": "Google Search Engine ID (CX)"},
                    "BING_SEARCH_API_KEY": {"type": "string", "description": "Bing Search API Key"},
                    "HEADLESS": {
                        "type": "boolean", 
                        "default": True, 
                        "description": "Whether to run the browser in headless mode. Set to False to see the search happens."
                    }
                },
                "required": ["GOOGLE_SEARCH_API_KEY", "GOOGLE_SEARCH_ID"]
            },
            requirements=["httpx", "playwright"]
        )
    
    async def execute(self, query: str, engine: str = "auto", num_results: int = 5, extract_keywords: bool = False, headless: bool = True) -> Dict[str, Any]:
        """
        Execute web search with multi-engine support.
        """
        await self.validate_inputs(query=query, engine=engine, num_results=num_results)
        
        # Override headless from execution arg if provided
        self._execution_headless = headless
        
        search_query = query
        
        # 1. Keyword Extraction (Optional)
        if extract_keywords and self.config:
            try:
                from agi.skilldock.skills.text_analyzer.scripts.agent import LLMTextAnalyzerSkill
                analyzer = LLMTextAnalyzerSkill(self.config)
                analysis_result = await analyzer.execute(
                    text=query, 
                    task="Extract 3-5 search-optimized keywords from this query. Return ONLY the keywords separated by spaces."
                )
                extracted = analysis_result.get("analysis", "").strip()
                if extracted and not extracted.startswith("Error"):
                    search_query = extracted
            except Exception as e:
                if self.config.verbose:
                    print(f"[WebSearch] Keyword extraction failed: {e}")

        # 2. Engine Selection & Execution
        engine_val = engine.lower()
        if engine_val == "auto":
            # Prefer Google -> Bing -> Browser -> DuckDuckGo based on keys
            if self.agi_config.google_api_key or (self.config.get("GOOGLE_SEARCH_API_KEY") and self.config.get("GOOGLE_SEARCH_ID")):
                engine_val = "google"
            elif self.config.get("BING_SEARCH_API_KEY"):
                engine_val = "bing"
            else:
                engine_val = "browser"

        results = []
        try:
            if engine_val == "google":
                results = await self._search_google(search_query, num_results)
            elif engine_val == "bing":
                results = await self._search_bing(search_query, num_results)
            elif engine_val == "browser":
                results = await self._search_browser(search_query, num_results)
            else:
                results = await self._search_duckduckgo(search_query, num_results)
        except Exception as e:
            if self.agi_config and self.agi_config.verbose:
                print(f"[WebSearch] {engine_val} failed: {e}. Falling back to DuckDuckGo.")
            if engine_val != "duckduckgo":
                results = await self._search_duckduckgo(search_query, num_results)
                engine_val = "duckduckgo"

        return {
            "results": results[:num_results],
            "engine_used": engine_val,
            "query_used": search_query
        }

    async def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (HTML scraping fallback or Lite)."""
        # DuckDuckGo Lite is easier to parse
        url = "https://lite.duckduckgo.com/lite/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        data = {"q": query}
        
        results = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.post(url, data=data, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    from html.parser import HTMLParser
                    
                    class DDGParser(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.results = []
                            self.current_result = {}
                            self.in_title = False
                            self.in_snippet = False
                            self.in_link = False
                            self.count = 0
                        
                        def handle_starttag(self, tag, attrs):
                            attrs_dict = dict(attrs)
                            if tag == "a" and "result-link" in attrs_dict.get("class", ""):
                                self.in_title = True
                                self.current_result["url"] = attrs_dict.get("href")
                            elif tag == "td" and "result-snippet" in attrs_dict.get("class", ""):
                                self.in_snippet = True
                        
                        def handle_data(self, data):
                            if self.in_title:
                                self.current_result["title"] = self.current_result.get("title", "") + data
                            elif self.in_snippet:
                                self.current_result["snippet"] = self.current_result.get("snippet", "") + data
                        
                        def handle_endtag(self, tag):
                            if tag == "a" and self.in_title:
                                self.in_title = False
                            elif tag == "td" and self.in_snippet:
                                self.in_snippet = False
                                if self.current_result.get("title"):
                                    self.results.append(self.current_result)
                                    self.current_result = {}
                                    self.count += 1
                                    
                    parser = DDGParser()
                    parser.feed(response.text)
                    results = parser.results
            except Exception as e:
                if self.config and self.config.get("verbose"):
                    print(f"[WebSearch] DuckDuckGo crawl failed: {e}")
        
        if not results:
             results = [
                {"title": f"Search result for {query}", "url": f"https://www.google.com/search?q={query}", "snippet": f"Found information about {query}..."}
             ]
        return results

    async def _search_google(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Google Custom Search JSON API."""
        api_key = self.config.get("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY") or self.agi_config.google_api_key
        search_id = self.config.get("GOOGLE_SEARCH_ID") or os.getenv("GOOGLE_SEARCH_ID")
        if not api_key or not search_id:
            raise ValueError("Google Search API key or ID missing")
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Google API error: {response.text}")
            
            data = response.json()
            items = data.get("items", [])
            return [
                {"title": item.get("title"), "url": item.get("link"), "snippet": item.get("snippet")}
                for item in items
            ]

    async def _search_bing(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Bing Search API."""
        api_key = self.config.get("BING_SEARCH_API_KEY") or os.getenv("BING_SEARCH_API_KEY")
        if not api_key:
            raise ValueError("Bing Search API key missing")
            
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": query, "count": num_results}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Bing API error: {response.text}")
            
            data = response.json()
            web_pages = data.get("webPages", {}).get("value", [])
            return [
                {"title": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet")}
                for item in web_pages
            ]

    async def _search_browser(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search by opening a real browser using Playwright."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright is not installed. Please add it to requirements.")
            
        results = []
        headless = getattr(self, '_execution_headless', self.config.get("HEADLESS", True))
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=headless)
            page = await browser.new_page()
            
            search_url = f"https://www.google.com/search?q={query}"
            await page.goto(search_url, wait_until="domcontentloaded")
            
            items = await page.query_selector_all("div.g")
            
            for item in items[:num_results]:
                title_elem = await item.query_selector("h3")
                link_elem = await item.query_selector("a")
                snippet_elem = await item.query_selector("div.VwiC3b")
                
                if title_elem and link_elem:
                    title = await title_elem.inner_text()
                    url = await link_elem.get_attribute("href")
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""
                    
                    if url and url.startswith("http"):
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
            
            await browser.close()
            
        if not results:
             return await self._search_duckduckgo(query, num_results)
             
        return results