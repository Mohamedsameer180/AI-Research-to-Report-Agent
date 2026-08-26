#!/usr/bin/env python3
"""
Actual Google ADK Tool for Web Scraping
Implements a real tool that can be used by Google ADK agents to scrape and extract content from web pages
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
import urllib.parse


class WebScraperTool(BaseTool):
    """A Google ADK tool for scraping content from specific web URLs"""
    
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Scrape and extract content from a specific web URL"
        )
    
    async def _run_async_impl(self, *, args: Dict[str, Any], tool_context: ToolContext) -> Dict[str, Any]:
        """
        Execute the web scraping tool
        
        Args:
            args: Dictionary containing 'url' (str) and optionally 'selector' (str for CSS selector)
            tool_context: Context for the tool execution
            
        Returns:
            Dictionary with scraped content
        """
        url = args.get("url", "")
        selector = args.get("selector", None)  # CSS selector for specific elements
        
        if not url:
            return {
                "status": "error",
                "error_message": "URL parameter is required"
            }
        
        # Validate URL format
        try:
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                return {
                    "status": "error",
                    "error_message": "Invalid URL format"
                }
        except Exception:
            return {
                "status": "error",
                "error_message": "Invalid URL format"
            }
        
        try:
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fetch the webpage
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            if selector:
                # Try to extract content using CSS selector
                try:
                    elements = soup.select(selector)
                    if elements:
                        text_content = '\n'.join([elem.get_text(strip=True) for elem in elements])
                    else:
                        text_content = "No elements found matching the selector"
                except Exception:
                    # Fallback to full text if selector fails
                    text_content = soup.get_text()
                    selector_used = None
            else:
                # Extract all text content
                text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit content length for practicality
            if len(cleaned_text) > 5000:
                cleaned_text = cleaned_text[:5000] + "\n\n[Content truncated for length]"
            
            # Extract title if available
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "No title found"
            
            # Store evidence in session state
            tool_context.state["last_scraped_url"] = url
            tool_context.state["last_scraped_content_length"] = len(cleaned_text)
            
            return {
                "status": "success",
                "url": url,
                "title": title_text,
                "content": cleaned_text,
                "content_length": len(cleaned_text),
                "evidence": [
                    f"Web page scraped: {url}",
                    f"Title: {title_text}",
                    f"Content extracted: {len(cleaned_text)} characters"
                ]
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error_message": f"Failed to fetch web page: {str(e)}",
                "evidence": [f"Web scraping attempt failed for URL: {url}"]
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Web scraping failed: {str(e)}",
                "evidence": [f"Web scraping attempt failed for URL: {url}"]
            }


# Create a singleton instance for use by agents
web_scraper_tool = WebScraperTool()
