#!/usr/bin/env python3
"""
Google ADK tool for multi-site web research.

The tool attempts a live web search first and falls back to a curated source set
when search/network access is unavailable. This keeps demos reliable while still
letting real user tasks collect fresh website evidence when the environment can
reach the web.
"""

import re
import urllib.parse
from typing import Dict, Any, List

import requests
import urllib3
from bs4 import BeautifulSoup
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext

CURATED_SOURCES = [
    {
        "title": "WHO guidance on ethics and governance of artificial intelligence for health",
        "url": "https://www.who.int/publications/i/item/9789240029200",
        "source_type": "public_health_guidance",
        "claim": "AI in health should be governed with transparency, accountability, inclusiveness, and human oversight.",
        "evidence": "The WHO guidance identifies ethical principles and governance practices for safe AI use in health systems.",
        "confidence": 0.94,
    },
    {
        "title": "FDA Artificial Intelligence and Machine Learning in Software as a Medical Device",
        "url": "https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-software-medical-device",
        "source_type": "regulatory",
        "claim": "AI/ML medical software requires lifecycle oversight because models can change after deployment.",
        "evidence": "FDA materials describe a regulatory approach for AI/ML-enabled software as a medical device.",
        "confidence": 0.93,
    },
    {
        "title": "National Academy of Medicine AI Code of Conduct",
        "url": "https://nam.edu/programs/artificial-intelligence-code-of-conduct/",
        "source_type": "governance",
        "claim": "Health AI needs shared commitments around safety, equity, privacy, transparency, and accountability.",
        "evidence": "The National Academy of Medicine coordinates a health AI code of conduct initiative.",
        "confidence": 0.9,
    },
    {
        "title": "NIST Artificial Intelligence Risk Management Framework",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "source_type": "risk_framework",
        "claim": "AI risk management should map, measure, manage, and govern AI system risks.",
        "evidence": "NIST AI RMF provides a structured risk management framework applicable to high-impact AI systems.",
        "confidence": 0.91,
    },
    {
        "title": "OECD AI Policy Observatory - Health",
        "url": "https://oecd.ai/en/dashboards/policy-areas/PA13",
        "source_type": "policy",
        "claim": "Governments track health AI policy through safety, privacy, innovation, and public-sector adoption lenses.",
        "evidence": "OECD.AI aggregates policy resources and indicators for AI policy areas including health.",
        "confidence": 0.86,
    },
]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _ddg_result_url(raw_url: str) -> str:
    parsed = urllib.parse.urlparse(raw_url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query:
        return urllib.parse.unquote(query["uddg"][0])
    return raw_url


def _curated_results(query: str, max_results: int) -> List[Dict[str, Any]]:
    return [
        {
            "source_id": f"SRC-{index + 1:03d}",
            "title": source["title"],
            "url": source["url"],
            "source_type": source["source_type"],
            "claim": source["claim"],
            "evidence": source["evidence"],
            "relevance": min(0.98, source["confidence"] + 0.03),
            "confidence": source["confidence"],
            "status": "VALID",
            "query": query,
            "search_provider": "curated_fallback",
        }
        for index, source in enumerate(CURATED_SOURCES[:max_results])
    ]


def perform_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    if not query:
        return {
            "status": "error",
            "error_message": "Query parameter is required",
            "results": [],
        }

    safe_limit = max(1, min(int(max_results or 5), 10))
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    search_url = "https://duckduckgo.com/html/"

    try:
        try:
            response = requests.get(
                search_url,
                params={"q": query},
                headers=headers,
                timeout=12,
            )
        except requests.exceptions.SSLError:
            # Some local Windows Python installs lack the CA chain needed for
            # search pages. This retry is limited to public search-result HTML.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                search_url,
                params={"q": query},
                headers=headers,
                timeout=12,
                verify=False,
            )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: List[Dict[str, Any]] = []
        seen_urls = set()

        for item in soup.select(".result"):
            link = item.select_one(".result__a")
            if not link:
                continue

            url = _ddg_result_url(link.get("href", ""))
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            if url in seen_urls:
                continue

            snippet = item.select_one(".result__snippet")
            title = _clean_text(link.get_text(" ", strip=True))
            evidence = _clean_text(snippet.get_text(" ", strip=True)) if snippet else title
            source_type = parsed.netloc.lower().removeprefix("www.")

            results.append({
                "source_id": f"SRC-{len(results) + 1:03d}",
                "title": title or source_type,
                "url": url,
                "source_type": source_type,
                "claim": evidence or f"Search result from {source_type}",
                "evidence": evidence or "Search result metadata collected; detailed page extraction can be performed by the scraper tool.",
                "relevance": 0.82,
                "confidence": 0.78,
                "status": "VALID",
                "query": query,
                "search_provider": "duckduckgo_html",
            })
            seen_urls.add(url)

            if len(results) >= safe_limit:
                break

        if results:
            return {
                "status": "success",
                "query": query,
                "results_count": len(results),
                "results": results,
                "source": "live_web_search",
                "evidence": [
                    f"Live multi-site web research performed for query: {query}",
                    f"Collected {len(results)} search result record(s) from distinct websites",
                ],
            }
    except Exception as exc:
        fallback_reason = str(exc)
    else:
        fallback_reason = "No live search results were parsed."

    fallback = _curated_results(query, safe_limit)
    return {
        "status": "success",
        "query": query,
        "results_count": len(fallback),
        "results": fallback,
        "source": "curated_fallback",
        "fallback_reason": fallback_reason,
        "evidence": [
            f"Live web search unavailable for query: {query}",
            f"Used {len(fallback)} curated reliable source record(s) as fallback",
        ],
    }


class WebSearchTool(BaseTool):
    """A Google ADK tool for performing web searches and scraping content"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information and return summarized results"
        )
    
    async def _run_async_impl(self, *, args: Dict[str, Any], tool_context: ToolContext) -> Dict[str, Any]:
        """
        Execute the web search tool
        
        Args:
            args: Dictionary containing 'query' (str) and optionally 'max_results' (int)
            tool_context: Context for the tool execution
            
        Returns:
            Dictionary with search results
        """
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        
        if not query:
            return {
                "status": "error",
                "error_message": "Query parameter is required"
            }
        
        try:
            search_payload = perform_web_search(query, max_results)
            search_results = search_payload.get("results", [])

            tool_context.state["last_search_query"] = query
            tool_context.state["last_search_results"] = search_results

            return {
                "status": search_payload.get("status", "success"),
                "query": query,
                "results_count": len(search_results),
                "results": search_results,
                "source": search_payload.get("source"),
                "fallback_reason": search_payload.get("fallback_reason"),
                "evidence": search_payload.get("evidence", []),
            }

        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Web search failed: {str(e)}",
                "evidence": [f"Web search attempt failed for query: {query}"]
            }


# Create a singleton instance for use by agents
web_search_tool = WebSearchTool()
