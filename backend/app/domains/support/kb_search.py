"""
Knowledge Base & FAQ Search

Simple keyword-based search with TF-IDF-like scoring.
Future: semantic search with embeddings.
"""

import uuid
import re
from typing import List, Dict
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.support.service import SupportService


async def search_kb_and_faq(
    db: AsyncSession,
    business_id: uuid.UUID,
    query: str,
    top_k: int = 3,
) -> List[Dict]:
    """
    Search FAQ and KB articles by keyword relevance.

    Returns list of dicts with: id, title, content, type (faq|kb), score
    """
    svc = SupportService(db)

    # Fetch all active FAQ and KB for this business
    faqs = await svc.list_faqs(business_id=business_id)
    kb_articles = await svc.list_kb_articles(business_id=business_id)

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results = []

    for faq in faqs:
        text = f"{faq.question} {faq.answer} {faq.tags or ''}"
        score = _score(query_tokens, text)
        if score > 0:
            results.append({
                "id": str(faq.id),
                "title": faq.question,
                "content": faq.answer,
                "type": "faq",
                "score": score,
            })

    for article in kb_articles:
        text = f"{article.title} {article.content} {article.tags or ''}"
        score = _score(query_tokens, text)
        if score > 0:
            results.append({
                "id": str(article.id),
                "title": article.title,
                "content": article.content,
                "type": "kb",
                "score": score,
            })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _tokenize(text: str) -> List[str]:
    """Simple tokenization: lowercase, remove punctuation, filter stopwords."""
    stopwords = {
        "el", "la", "los", "las", "un", "una", "de", "del", "al", "y", "o",
        "en", "con", "por", "para", "que", "es", "son", "the", "a", "an",
        "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are",
    }
    tokens = re.findall(r"\b[a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,}\b", text.lower())
    return [t for t in tokens if t not in stopwords]


def _score(query_tokens: List[str], document: str) -> float:
    """Simple TF-IDF-like scoring."""
    doc_tokens = _tokenize(document)
    if not doc_tokens:
        return 0.0

    doc_counter = Counter(doc_tokens)
    query_counter = Counter(query_tokens)

    score = 0.0
    for token in query_counter:
        tf = doc_counter.get(token, 0) / len(doc_tokens)
        # Simple IDF: rare tokens get higher weight
        idf = 1.0 + (1.0 / (1 + doc_counter.get(token, 0)))
        score += tf * idf * query_counter[token]

    # Normalize
    return score / len(query_tokens)
