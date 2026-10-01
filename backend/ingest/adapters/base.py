"""Base adapter contracts for listing-to-document source capture.

Normative source:
- docs/02_P0_source_acquisition.md §5.5 (Adapter plug-in contract)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListingItem:
    """A single record extracted from an HTML listing page."""

    record_key: str
    detail_url: str | None
    file_url: str
    source_metadata: dict[str, Any]
    page_number: int
    row_index: int


class BaseListingAdapter(ABC):
    """Abstract base class for all listing-based crawlers."""

    adapter_id: str
    version: str
    source_id: str

    @abstractmethod
    def build_page_url(self, section: str, page_number: int) -> str:
        """Construct the URL for a specific listing section and page number."""
        ...

    @abstractmethod
    def parse_listing_page(self, html: str, section: str, page_number: int) -> list[ListingItem]:
        """Extract all items from a single listing page HTML."""
        ...

    @abstractmethod
    def detect_captcha(self, html: str) -> bool:
        """Return True if any CAPTCHA or human challenge markup is present."""
        ...

    @abstractmethod
    def detect_layout_drift(self, html: str, items: list[ListingItem]) -> bool:
        """Return True if the page layout has broken or failed to yield expected items."""
        ...

    def is_soft_error(self, status_code: int, body: bytes) -> bool:
        """Check for soft error pages (200 status with error body)."""
        return False
