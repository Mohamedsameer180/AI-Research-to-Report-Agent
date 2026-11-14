"""Google ADK Paper Extractor Agent.

Specialized ADK Agent for extracting structured paper records (objectives,
methodologies, evaluations, empirical results, limitations) and mapping each claim
to verbatim citations (<=300 chars) with pdf_page and printed_page numbers.
"""

import os
from typing import Optional
from google.adk.agents import Agent

EXTRACTION_AGENT_INSTRUCTION = """
You are the PaperExtractorAgent for TP01: AI Research Paper Intelligence Platform.
Your mission is to extract structured, verifiable facts from research papers section by section.

CORE OPERATIONAL RULES:
1. ZERO HALLUCINATION: Every factual assertion MUST be supported by a VERBATIM excerpt (quote <= 300 chars).
   If no exact supporting quote exists in the source text, leave the field null.
2. VERBATIM ACCURACY: The quote must exist word-for-word in the text of the specified page.
3. PAGE ACCURACY: Record the physical 1-based pdf_page and the printed_page label if visible.
4. MODEL ANALYSIS SEPARATION: Clearly distinguish model synthesis (contributions, strengths/weaknesses)
   from verbatim extracted facts.
5. NO FABRICATED METRICS: Never invent benchmark scores, numbers, or baseline comparisons.
"""


def create_paper_extractor_agent(
    model: Optional[str] = None,
    name: str = "PaperExtractorAgent",
) -> Agent:
    """Instantiates the Google ADK PaperExtractorAgent."""
    agent_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return Agent(
        name=name,
        model=agent_model,
        instruction=EXTRACTION_AGENT_INSTRUCTION,
        tools=[],
    )

