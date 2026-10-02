"""Hidden-text detector for security and untrusted document hygiene.

Normative sources:
- docs/mvp/00_mvp_spec.md §2 (untrusted documents stay data; hidden-text flags)
- docs/03_P1_ingestion_parsing.md §5.2 item 4:
  White text, off-page text, zero-size fonts, and text layers that disagree with render.
  Flagged text is dropped from claimable anchors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pymupdf


@dataclass(frozen=True, slots=True)
class HiddenTextRegion:
    page_number: int
    text: str
    reason: str  # WHITE_TEXT | OFF_PAGE | TINY_FONT | INVISIBLE_MODE
    bbox: list[float]
    char_count: int


@dataclass(frozen=True, slots=True)
class HiddenTextResult:
    hidden_text_detected: bool
    flags: list[str]
    regions: list[HiddenTextRegion]
    clean_blocks: list[dict[str, Any]]


def inspect_page_for_hidden_text(
    page: pymupdf.Page, page_number: int
) -> tuple[list[str], list[HiddenTextRegion], list[dict[str, Any]]]:
    """Inspect a PyMuPDF page for adversarial or hidden text.

    Returns (flags, hidden_regions, clean_blocks).
    """
    flags: set[str] = set()
    hidden_regions: list[HiddenTextRegion] = []
    clean_blocks: list[dict[str, Any]] = []

    rect = page.rect
    page_w = rect.width
    page_h = rect.height

    page_dict = page.get_text("dict")  # type: ignore[no-untyped-call]
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # Text block
            continue

        clean_lines = []
        for line in block.get("lines", []):
            clean_spans = []
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text.strip():
                    continue

                bbox = span.get("bbox", [0, 0, 0, 0])
                size = span.get("size", 10.0)
                color = span.get("color", 0)

                # 1. Tiny font (< 1.0 pt)
                if size < 1.0:
                    flags.add("TINY_FONT")
                    hidden_regions.append(
                        HiddenTextRegion(
                            page_number=page_number,
                            text=text,
                            reason="TINY_FONT",
                            bbox=[round(c, 2) for c in bbox],
                            char_count=len(text),
                        )
                    )
                    continue

                # 2. White text (0xFFFFFF or RGB near 255, 255, 255)
                # In PyMuPDF sRGB color is an integer 0xRRGGBB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
                if r >= 248 and g >= 248 and b >= 248:
                    flags.add("WHITE_TEXT")
                    hidden_regions.append(
                        HiddenTextRegion(
                            page_number=page_number,
                            text=text,
                            reason="WHITE_TEXT",
                            bbox=[round(c, 2) for c in bbox],
                            char_count=len(text),
                        )
                    )
                    continue

                # 3. Off-page text (outside or extending past [0, 0, page_w, page_h])
                x0, y0, x1, y1 = bbox
                if x0 < 0 or y0 < 0 or x1 > page_w or y1 > page_h:
                    flags.add("OFF_PAGE")
                    hidden_regions.append(
                        HiddenTextRegion(
                            page_number=page_number,
                            text=text,
                            reason="OFF_PAGE",
                            bbox=[round(c, 2) for c in bbox],
                            char_count=len(text),
                        )
                    )
                    continue

                # Clean span
                clean_spans.append(span)

            if clean_spans:
                line_copy = dict(line)
                line_copy["spans"] = clean_spans
                clean_lines.append(line_copy)

        if clean_lines:
            block_copy = dict(block)
            block_copy["lines"] = clean_lines
            clean_blocks.append(block_copy)

    return sorted(flags), hidden_regions, clean_blocks
