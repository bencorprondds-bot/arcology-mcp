"""
Arcology Knowledge Node — Content Index Loader
================================================
Loads the content-index.json from local file or remote URL.
Local file (data/content-index.json) is preferred when present.
Refreshes every 5 minutes.
"""

from __future__ import annotations
import asyncio
import json
import os
import time
import logging
from pathlib import Path
from typing import Optional

import httpx
from models import ContentIndex

logger = logging.getLogger("arcology-mcp")

# Default to GitHub-hosted data (always available, independent of site uptime)
# Override with INDEX_URL env var to point at lifewithai.ai or local file
REMOTE_URL = "https://raw.githubusercontent.com/bencorprondds-bot/arcology-mcp/main/data/content-index.json"
LOCAL_PATH = Path(__file__).parent / "data" / "content-index.json"

_cached_index: Optional[ContentIndex] = None
_last_fetch: float = 0
_fetch_interval: float = 300  # 5 minutes
_use_local: bool = True  # prefer local file when it exists


async def get_index() -> ContentIndex:
    """Get the content index, loading from local file or remote URL."""
    global _cached_index, _last_fetch

    now = time.time()
    if _cached_index is not None and (now - _last_fetch) < _fetch_interval:
        return _cached_index

    # Try local file first (preferred for dev, always up-to-date)
    if _use_local and LOCAL_PATH.exists():
        try:
            data = json.loads(LOCAL_PATH.read_text(encoding="utf-8"))
            _cached_index = ContentIndex(**data)
            _last_fetch = now
            logger.info(
                f"Content index loaded from local file: {_cached_index.aggregate_stats.total_entries} entries, "
                f"{len(_cached_index.domains)} domains"
            )
            return _cached_index
        except Exception as e:
            logger.warning(f"Failed to load local index: {e}, falling back to remote")

    # Fall back to remote URL
    index_url = os.environ.get("INDEX_URL", REMOTE_URL)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(index_url)
            response.raise_for_status()
            data = response.json()
            _cached_index = ContentIndex(**data)
            _last_fetch = now
            logger.info(
                f"Content index loaded from remote: {_cached_index.aggregate_stats.total_entries} entries, "
                f"{len(_cached_index.domains)} domains"
            )
            return _cached_index
    except Exception as e:
        logger.error(f"Failed to fetch content index: {e}")
        if _cached_index is not None:
            logger.warning("Using stale cached index")
            return _cached_index
        raise RuntimeError(
            f"Cannot load content index from {index_url}: {e}"
        ) from e


def set_index_url(url: str) -> None:
    """Override the remote index URL."""
    global REMOTE_URL
    REMOTE_URL = url
    logger.info(f"Remote index URL set to: {url}")


def set_local_mode(enabled: bool) -> None:
    """Enable or disable local file preference."""
    global _use_local
    _use_local = enabled
    logger.info(f"Local file mode: {'enabled' if enabled else 'disabled'}")
