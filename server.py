"""
Arcology Knowledge Node — MCP Server
======================================
Phase 0: Read-only access to the engineering knowledge base.

6 tools for AI agents to discover, search, and reason about
the collaborative engineering knowledge base for Arcology One.

Transport: SSE (Server-Sent Events)
Data source: content-index.json from the main site
"""

from __future__ import annotations
import os
import logging
from typing import Optional

from fastmcp import FastMCP

from index_loader import get_index, set_index_url
from search import search_entries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("arcology-mcp")

# Allow overriding the index URL for local dev
index_url = os.environ.get("INDEX_URL")
if index_url:
    set_index_url(index_url)

# Create the MCP server
mcp = FastMCP(
    name="Arcology Knowledge Node",
    instructions="""You are connected to the Arcology Knowledge Node — a collaborative
engineering knowledge base for Arcology One, a speculative mile-high city designed to
house 10 million people.

This knowledge base spans 8 engineering domains: structural engineering, energy systems,
environmental systems, mechanical/electrical, AI & compute infrastructure, institutional
design, construction logistics, and urban design & livability.

Each knowledge entry has:
- KEDL level (100-500): Knowledge Entry Development Level, from Conceptual to As-Built
- Confidence level (1-5): from Conjectured to Validated
- Quantitative parameters with units and individual confidence ratings
- Cross-domain references showing dependencies between systems
- Open questions representing the frontier of what needs to be figured out

Use these tools to explore the knowledge base, find relevant entries, check cross-domain
consistency of parameters, and identify open questions where your analysis could contribute.

This is Phase 0 (read-only). A contribution pipeline is coming in Phase 2.""",
)


@mcp.tool()
async def read_node(domain: str, slug: str) -> dict:
    """Retrieve a full knowledge entry by domain and slug.

    Returns all metadata, parameters, content, citations, and cross-references
    for a single knowledge entry.

    Args:
        domain: The engineering domain (e.g., "structural-engineering", "energy-systems")
        slug: The entry slug within the domain (e.g., "superstructure/primary-geometry")
    """
    index = await get_index()

    entry_id = f"{domain}/{slug}"
    for entry in index.entries:
        if entry.id == entry_id:
            return entry.model_dump()

    # Try matching by domain + slug
    for entry in index.entries:
        if entry.domain == domain and entry.slug == slug:
            return entry.model_dump()

    return {"error": f"Entry not found: {domain}/{slug}"}


@mcp.tool()
async def search_knowledge(
    query: str,
    domain: Optional[str] = None,
    kedl_min: Optional[int] = None,
    confidence_min: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """Search the knowledge base with optional filters.

    Full-text search across all knowledge entries. Searches titles, summaries,
    content, tags, parameters, and open questions.

    Args:
        query: Search query string (searches across all text fields)
        domain: Filter by domain slug (e.g., "energy-systems")
        kedl_min: Minimum KEDL level (100, 200, 300, 350, 400, 500)
        confidence_min: Minimum confidence level (1-5)
        type: Filter by entry type ("concept", "analysis", "specification", "reference", "open-question")
        limit: Maximum results to return (default 20)
    """
    index = await get_index()

    results = search_entries(
        index.entries,
        query=query,
        domain=domain,
        kedl_min=kedl_min,
        confidence_min=confidence_min,
        entry_type=type,
        limit=limit,
    )

    # Return summaries (strip content to reduce token count)
    return {
        "query": query,
        "filters": {
            "domain": domain,
            "kedl_min": kedl_min,
            "confidence_min": confidence_min,
            "type": type,
        },
        "count": len(results),
        "results": [
            {
                "id": e.id,
                "title": e.title,
                "domain": e.domain,
                "subdomain": e.subdomain,
                "kedl": e.kedl,
                "confidence": e.confidence,
                "entry_type": e.entry_type,
                "summary": e.summary,
                "tags": e.tags,
                "parameter_count": len(e.parameters),
                "open_question_count": len(e.open_questions),
                "citation_count": len(e.citations),
                "cross_reference_count": len(e.cross_references),
            }
            for e in results
        ],
    }


@mcp.tool()
async def list_domains() -> dict:
    """List all engineering domains with summary statistics.

    Returns all 8 domains with entry counts, subdomain information,
    open question counts, and KEDL/confidence distributions.
    """
    index = await get_index()

    domains = []
    for dm in index.domains:
        stats = next((ds for ds in index.domain_stats if ds.slug == dm.slug), None)
        domains.append({
            "slug": dm.slug,
            "name": dm.name,
            "description": dm.description,
            "color": dm.color,
            "subdomains": [
                {"slug": s.slug, "name": s.name, "description": s.description}
                for s in dm.subdomains
            ],
            "stats": stats.model_dump() if stats else None,
        })

    return {
        "domain_count": len(domains),
        "total_entries": index.aggregate_stats.total_entries,
        "domains": domains,
    }


@mcp.tool()
async def get_open_questions(
    domain: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get unanswered engineering questions from the knowledge base.

    These represent the frontier of what needs to be figured out.
    Each question is linked to the entry that raised it.

    Args:
        domain: Filter by domain slug (optional)
        limit: Maximum questions to return (default 50)
    """
    index = await get_index()

    entries = index.entries
    if domain:
        entries = [e for e in entries if e.domain == domain]

    questions = []
    for entry in entries:
        for q in entry.open_questions:
            questions.append({
                "question": q,
                "entry_id": entry.id,
                "entry_title": entry.title,
                "domain": entry.domain,
                "subdomain": entry.subdomain,
                "kedl": entry.kedl,
                "confidence": entry.confidence,
            })

    limited = questions[:limit]

    return {
        "count": len(limited),
        "total": len(questions),
        "domain_filter": domain,
        "questions": limited,
    }


@mcp.tool()
async def get_entry_parameters(
    domain: Optional[str] = None,
    parameter_name: Optional[str] = None,
) -> dict:
    """Get quantitative parameters from knowledge entries.

    Use this for cross-domain consistency checking. Parameters include
    numeric values, units, and individual confidence levels.

    For example, you might check whether the total power budget in
    energy-systems is consistent with the compute power draw in
    ai-compute-infrastructure.

    Args:
        domain: Filter by domain slug (optional)
        parameter_name: Filter by parameter name substring (optional)
    """
    index = await get_index()

    entries = index.entries
    if domain:
        entries = [e for e in entries if e.domain == domain]

    parameters = []
    for entry in entries:
        for p in entry.parameters:
            if parameter_name and parameter_name.lower() not in p.name.lower():
                continue
            parameters.append({
                "name": p.name,
                "value": p.value,
                "unit": p.unit,
                "confidence": p.confidence,
                "entry_id": entry.id,
                "entry_title": entry.title,
                "domain": entry.domain,
                "subdomain": entry.subdomain,
            })

    return {
        "count": len(parameters),
        "filters": {
            "domain": domain,
            "parameter_name": parameter_name,
        },
        "parameters": parameters,
    }


@mcp.tool()
async def get_domain_stats() -> dict:
    """Get aggregate platform statistics.

    Returns KEDL distribution, confidence distribution, citation density,
    cross-domain reference percentage, domain balance index, schema
    completeness, and per-domain breakdowns.

    All metrics are computed at build time from content files.
    """
    index = await get_index()

    return {
        "generated_at": index.generated_at,
        "aggregate": index.aggregate_stats.model_dump(),
        "domains": [ds.model_dump() for ds in index.domain_stats],
    }


def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "sse":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        logger.info(f"Starting MCP server (SSE) on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting MCP server (stdio)")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
