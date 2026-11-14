"""
Query expansion service for academic research RAG.
Produces multi-query variations using domain-aware synonym expansion,
acronym resolution, and keyword focalization.
"""
import re
from typing import List, Dict, Set

# Common academic domain acronyms and their expansions
ACRONYM_MAP: Dict[str, str] = {
    "llm": "large language model",
    "llms": "large language models",
    "rag": "retrieval augmented generation",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "rl": "reinforcement learning",
    "sota": "state of the art",
    "cnn": "convolutional neural network",
    "cnns": "convolutional neural networks",
    "rnn": "recurrent neural network",
    "rnns": "recurrent neural networks",
    "bert": "bidirectional encoder representations transformers",
    "vit": "vision transformer",
    "vits": "vision transformers",
    "gan": "generative adversarial network",
    "gans": "generative adversarial networks",
    "vae": "variational autoencoder",
    "vaes": "variational autoencoders",
    "cot": "chain of thought",
    "rlhf": "reinforcement learning from human feedback",
    "lora": "low rank adaptation",
    "dpo": "direct preference optimization",
}

# Academic intent keywords for variant synthesis
INTENT_SYNONYMS: Dict[str, List[str]] = {
    "limitation": ["weakness", "bottleneck", "constraint", "drawback", "failure case"],
    "limitations": ["weaknesses", "bottlenecks", "constraints", "drawbacks"],
    "methodology": ["approach", "proposed method", "architecture", "framework", "technique"],
    "method": ["approach", "technique", "algorithm", "model"],
    "result": ["finding", "performance", "benchmark score", "accuracy", "empirical evaluation"],
    "results": ["findings", "experimental results", "benchmarks", "evaluation metrics"],
    "objective": ["goal", "purpose", "aim", "research question"],
    "conclusion": ["summary", "future work", "takeaway", "implications"],
    "comparison": ["tradeoff", "versus", "outperform", "difference", "contrast"],
}


def expand_acronyms(text: str) -> str:
    """Expand recognized acronyms in the query string."""
    tokens = text.split()
    expanded_tokens = []
    for token in tokens:
        clean_token = re.sub(r"[^\w]", "", token.lower())
        if clean_token in ACRONYM_MAP:
            expanded_tokens.append(f"{token} ({ACRONYM_MAP[clean_token]})")
        else:
            expanded_tokens.append(token)
    return " ".join(expanded_tokens)


def generate_keyword_query(text: str) -> str:
    """Extract focal nouns and technical terms for BM25 keyword matching."""
    # Remove common question filler phrases
    filler_patterns = [
        r"^(?:what\s+is|what\s+are|how\s+does|can\s+you\s+explain|tell\s+me\s+about|find\s+me|show\s+me)\b",
        r"\b(?:in\s+the\s+paper|according\s+to\s+the\s+authors|in\s+this\s+study)\b",
    ]
    cleaned = text
    for pat in filler_patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # Clean punctuation
    cleaned = re.sub(r"[?!.,;:]", " ", cleaned).strip()
    return re.sub(r"\s+", " ", cleaned)


def generate_multi_queries(query: str, max_variations: int = 3) -> List[str]:
    """
    Generate multiple distinct query formulations for hybrid retrieval:
    1. The raw user query
    2. Acronym-expanded technical query
    3. Keyword-focalized query with intent synonyms
    """
    queries = [query.strip()]
    seen: Set[str] = {query.strip().lower()}

    # Variation 1: Acronym expansion
    acronym_expanded = expand_acronyms(query)
    if acronym_expanded.lower() not in seen:
        queries.append(acronym_expanded)
        seen.add(acronym_expanded.lower())

    # Variation 2: Keyword query
    keyword_q = generate_keyword_query(query)
    if keyword_q and keyword_q.lower() not in seen:
        queries.append(keyword_q)
        seen.add(keyword_q.lower())

    # Variation 3: Academic intent substitution (e.g. "limitations" -> "weaknesses constraints")
    words = query.lower().split()
    synonym_injected = []
    has_sub = False
    for w in words:
        clean_w = re.sub(r"[^\w]", "", w)
        if clean_w in INTENT_SYNONYMS and not has_sub:
            syns = INTENT_SYNONYMS[clean_w][:2]
            synonym_injected.append(f"{w} {' '.join(syns)}")
            has_sub = True
        else:
            synonym_injected.append(w)

    if has_sub:
        syn_query = " ".join(synonym_injected)
        if syn_query.lower() not in seen:
            queries.append(syn_query)
            seen.add(syn_query.lower())

    return queries[:max_variations]

