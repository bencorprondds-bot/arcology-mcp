"""
Arcology Knowledge Node — Search Implementation
=================================================
Full-text search across knowledge entries.
Mirrors the TypeScript client-side search logic.
"""

from __future__ import annotations
from typing import Optional
from models import KnowledgeEntry


def search_entries(
    entries: list[KnowledgeEntry],
    query: Optional[str] = None,
    domain: Optional[str] = None,
    kedl_min: Optional[int] = None,
    confidence_min: Optional[int] = None,
    entry_type: Optional[str] = None,
    limit: int = 50,
) -> list[KnowledgeEntry]:
    """Search and filter knowledge entries."""
    results = list(entries)

    # Domain filter
    if domain:
        results = [e for e in results if e.domain == domain]

    # KEDL minimum filter
    if kedl_min is not None:
        results = [e for e in results if e.kedl >= kedl_min]

    # Confidence minimum filter
    if confidence_min is not None:
        results = [e for e in results if e.confidence >= confidence_min]

    # Entry type filter
    if entry_type:
        results = [e for e in results if e.entry_type == entry_type]

    # Full-text search
    if query and query.strip():
        terms = query.lower().split()
        results = [e for e in results if _matches_all_terms(e, terms)]
        # Sort by relevance (term frequency)
        results.sort(key=lambda e: -_score(e, terms))

    return results[:limit]


def _build_search_text(entry: KnowledgeEntry) -> str:
    """Build a searchable text string from all entry fields."""
    parts = [
        entry.title,
        entry.summary,
        entry.content,
        " ".join(entry.tags),
        " ".join(entry.open_questions),
        " ".join(entry.assumptions),
        " ".join(p.name for p in entry.parameters),
    ]
    return " ".join(parts).lower()


def _matches_all_terms(entry: KnowledgeEntry, terms: list[str]) -> bool:
    """Check if entry text contains all search terms."""
    text = _build_search_text(entry)
    return all(term in text for term in terms)


def _score(entry: KnowledgeEntry, terms: list[str]) -> int:
    """Score an entry based on term frequency."""
    text = _build_search_text(entry)
    return sum(text.count(term) for term in terms)
