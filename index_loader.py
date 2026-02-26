"""
Arcology Knowledge Node — Content Index Loader
================================================
Fetches and caches the content-index.json from the main site.
Refreshes every 5 minutes.
"""

from __future__ import annotations
import asyncio
import time
import logging
from typing import Optional

import httpx
from models import ContentIndex

logger = logging.getLogger("arcology-mcp")

# Default to the production URL; override with environment variable
INDEX_URL = "https://lifewithai.ai/content-index.json"

_cached_index: Optional[ContentIndex] = None
_last_fetch: float = 0
_fetch_interval: float = 300  # 5 minutes


async def get_index() -> ContentIndex:
    """Get the content index, fetching fresh data if cache is stale."""
    global _cached_index, _last_fetch

    now = time.time()
    if _cached_index is not None and (now - _last_fetch) < _fetch_interval:
        return _cached_index

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(INDEX_URL)
            response.raise_for_status()
            data = response.json()
            _cached_index = ContentIndex(**data)
            _last_fetch = now
            logger.info(
                f"Content index loaded: {_cached_index.aggregate_stats.total_entries} entries, "
                f"{len(_cached_index.domains)} domains"
            )
            return _cached_index
    except Exception as e:
        logger.error(f"Failed to fetch content index: {e}")
        if _cached_index is not None:
            logger.warning("Using stale cached index")
            return _cached_index
        raise RuntimeError(
            f"Cannot load content index from {INDEX_URL}: {e}"
        ) from e


def set_index_url(url: str) -> None:
    """Override the index URL (for local development)."""
    global INDEX_URL
    INDEX_URL = url
    logger.info(f"Index URL set to: {url}")
