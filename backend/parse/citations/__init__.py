"""Citations extraction, resolution, and deduplication package."""

from parse.citations.dedupe import check_dedupe_match, dedupe_and_merge, split_work
from parse.citations.extractor import ExtractedCitation, extract_citations_from_anchor
from parse.citations.resolver import promote_authoritative_alias, resolve_citation
from parse.citations.statutes import (
    ExtractedStatuteMention,
    extract_in_document_definitions,
    extract_statute_mentions_from_anchor,
)

__all__ = [
    "ExtractedCitation",
    "ExtractedStatuteMention",
    "extract_citations_from_anchor",
    "extract_statute_mentions_from_anchor",
    "extract_in_document_definitions",
    "resolve_citation",
    "promote_authoritative_alias",
    "check_dedupe_match",
    "dedupe_and_merge",
    "split_work",
]
