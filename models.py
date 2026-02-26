"""
Arcology Knowledge Node — Pydantic Response Models
====================================================
Structured response types for MCP tool outputs.
"""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class Author(BaseModel):
    id: str
    type: str  # "human" | "agent"
    model: Optional[str] = None


class Citation(BaseModel):
    id: str
    type: str  # peer-reviewed | standard | project-data | internal | expert-judgment
    title: str
    source: str
    year: int
    url: Optional[str] = None


class CrossReference(BaseModel):
    slug: str
    relationship: str  # depends-on | informs | contradicts | extends | alternative-to


class Parameter(BaseModel):
    name: str
    value: float
    unit: str
    confidence: int


class KnowledgeEntry(BaseModel):
    id: str
    title: str
    domain: str
    subdomain: str
    kedl: int
    confidence: int
    status: str
    created: str
    updated: str
    authors: list[Author] = []
    entry_type: str
    tags: list[str] = []
    summary: str
    citations: list[Citation] = []
    cross_references: list[CrossReference] = []
    open_questions: list[str] = []
    assumptions: list[str] = []
    parameters: list[Parameter] = []
    content: str = ""
    slug: str = ""


class SubdomainMeta(BaseModel):
    slug: str
    name: str
    description: str


class DomainMeta(BaseModel):
    name: str
    slug: str
    description: str
    color: str
    icon: str
    subdomains: list[SubdomainMeta] = []


class DomainStats(BaseModel):
    slug: str
    name: str
    color: str
    entry_count: int
    kedl_distribution: dict[str, int] = {}
    confidence_distribution: dict[str, int] = {}
    average_confidence: float = 0
    open_question_count: int = 0
    subdomain_count: int = 0
    last_updated: str = ""


class AggregateStats(BaseModel):
    total_entries: int = 0
    total_citations: int = 0
    total_cross_references: int = 0
    total_open_questions: int = 0
    total_parameters: int = 0
    kedl_distribution: dict[str, int] = {}
    confidence_distribution: dict[str, int] = {}
    average_citation_density: float = 0
    cross_domain_reference_percentage: float = 0
    domain_balance_index: float = 0
    schema_completeness: float = 0
    orphan_entry_rate: float = 0


class ContentIndex(BaseModel):
    generated_at: str
    entries: list[KnowledgeEntry] = []
    domains: list[DomainMeta] = []
    domain_stats: list[DomainStats] = []
    aggregate_stats: AggregateStats = AggregateStats()
