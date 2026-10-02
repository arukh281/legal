"""Page-level triage: text-layer validation, scan preprocessing, and OCR routing.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.2 (triage and text-layer validation)
- docs/mvp/04_stack_and_infra.md §2.7 (OCR triage)
- Session S05a Requirement 2, 3, 4, 9
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pymupdf
import structlog
from PIL import Image

from parse.hidden_text import HiddenTextRegion, inspect_page_for_hidden_text
from parse.ocr import OcrAdapter
from parse.preprocessor import (
    is_image_data,
    is_non_latin_text,
    preprocess_page_image,
    wrap_image_to_pdf,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PageLine:
    text: str
    bbox: list[float]  # [x0, y0, x1, y1] normalized to [0, 1]
    confidence: float
    words: list[dict[str, Any]]
    is_handwriting: bool = False
    source: str = "TEXT_LAYER"  # "TEXT_LAYER" | "OCR"


@dataclass(frozen=True, slots=True)
class TriagedPage:
    page_number: int
    text_source: str  # "TEXT_LAYER" | "OCR"
    ocr_conf: float
    lines: list[PageLine]
    full_text: str
    hidden_flags: list[str] = field(default_factory=list)
    hidden_regions: list[HiddenTextRegion] = field(default_factory=list)
    source_type: str = "BORN_DIGITAL"  # "BORN_DIGITAL" | "SCANNED" | "PHOTO"
    rotation_applied: int = 0
    dpi: int = 150
    is_lang_unsupported: bool = False
    preprocessing_meta: dict[str, Any] | None = None


class DocumentTriager:
    """Triages pages of raw PDF or image documents into clean text or OCR."""

    def __init__(self, ocr_adapter: OcrAdapter | None = None) -> None:
        self.ocr_adapter = ocr_adapter or OcrAdapter()

    def triage_document(
        self,
        raw_bytes: bytes,
        raw_id: str = "",
        mime_hint: str = "",
        use_ocr_cache: bool = True,
    ) -> list[TriagedPage]:
        """Triage each page: validate text layer, preprocess images, run OCR if needed."""
        # 1. Handle image inputs (JPG, PNG, TIFF, HEIC) per Requirement 9
        is_img, detected_mime = is_image_data(raw_bytes)
        initial_source_type = "BORN_DIGITAL"

        if is_img or mime_hint.startswith("image/"):
            raw_bytes, img_meta = wrap_image_to_pdf(raw_bytes, detected_mime or mime_hint)
            initial_source_type = img_meta.get("source_type", "SCANNED")

        doc = pymupdf.open(stream=raw_bytes, filetype="pdf")  # type: ignore[no-untyped-call]
        triaged_pages: list[TriagedPage] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            rect = page.rect
            page_w = max(1.0, rect.width)
            page_h = max(1.0, rect.height)

            # 2. Hidden text inspection
            hidden_flags, hidden_regions, clean_blocks = inspect_page_for_hidden_text(
                page, page_num
            )

            # 3. Text layer sanity check
            raw_text = page.get_text().strip()  # type: ignore[no-untyped-call]
            char_count = len(raw_text)

            printable_count = sum(1 for c in raw_text if c.isprintable())
            printable_ratio = printable_count / max(1, char_count)
            pua_count = sum(1 for c in raw_text if 0xE000 <= ord(c) <= 0xF8FF)
            pua_ratio = pua_count / max(1, char_count)

            # Check script on text layer
            is_non_latin = is_non_latin_text(raw_text)

            has_valid_text_layer = (
                char_count >= 50
                and printable_ratio >= 0.80
                and pua_ratio < 0.05
                and initial_source_type == "BORN_DIGITAL"
            )

            if has_valid_text_layer:
                # Text layer passes validation (TEXT_LAYER)
                page_lines: list[PageLine] = []
                for block in clean_blocks:
                    for line in block.get("lines", []):
                        line_text_parts = []
                        line_words = []
                        spans = line.get("spans", [])
                        for span in spans:
                            stext = span.get("text", "")
                            if not stext.strip():
                                continue
                            line_text_parts.append(stext)
                            sbbox = span.get("bbox", [0, 0, 0, 0])
                            # Normalize bbox to [0, 1]
                            norm_bbox = [
                                round(sbbox[0] / page_w, 4),
                                round(sbbox[1] / page_h, 4),
                                round(sbbox[2] / page_w, 4),
                                round(sbbox[3] / page_h, 4),
                            ]
                            line_words.append(
                                {
                                    "text": stext,
                                    "bbox": norm_bbox,
                                    "conf": 1.0,
                                    "is_handwriting": False,
                                }
                            )

                        if line_text_parts:
                            full_line_text = "".join(line_text_parts)
                            line_bbox = line.get("bbox", [0, 0, 0, 0])
                            norm_line_bbox = [
                                round(line_bbox[0] / page_w, 4),
                                round(line_bbox[1] / page_h, 4),
                                round(line_bbox[2] / page_w, 4),
                                round(line_bbox[3] / page_h, 4),
                            ]
                            page_lines.append(
                                PageLine(
                                    text=full_line_text,
                                    bbox=norm_line_bbox,
                                    confidence=1.0,
                                    words=line_words,
                                    is_handwriting=False,
                                    source="TEXT_LAYER",
                                )
                            )

                triaged_pages.append(
                    TriagedPage(
                        page_number=page_num,
                        text_source="TEXT_LAYER",
                        ocr_conf=1.0,
                        lines=page_lines,
                        full_text="\n".join(line.text for line in page_lines),
                        hidden_flags=hidden_flags,
                        hidden_regions=hidden_regions,
                        source_type="BORN_DIGITAL",
                        rotation_applied=0,
                        dpi=int(rect.width / 8.5 * 72) if rect.width > 0 else 150,
                        is_lang_unsupported=is_non_latin,
                    )
                )
            else:
                # Text layer is missing or failed sanity -> route to OCR
                pix = page.get_pixmap(dpi=150)
                pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                # Preprocess image (auto-rotate, deskew, upscale, contrast)
                processed_img, prep_meta = preprocess_page_image(pil_img)

                # Run OCR adapter
                ocr_result = self.ocr_adapter.process_page(
                    processed_img,
                    page_number=page_num,
                    raw_id=raw_id,
                    use_cache=use_ocr_cache,
                )

                page_lines = []
                for ocr_line in ocr_result.lines:
                    page_lines.append(
                        PageLine(
                            text=ocr_line.text,
                            bbox=ocr_line.bbox,
                            confidence=ocr_line.confidence,
                            words=[
                                {
                                    "text": w.text,
                                    "bbox": w.bbox,
                                    "conf": w.confidence,
                                    "is_handwriting": (w.text_type == "HANDWRITING"),
                                }
                                for w in ocr_line.words
                            ],
                            is_handwriting=(ocr_line.text_type == "HANDWRITING"),
                            source="OCR",
                        )
                    )

                source_type = (
                    initial_source_type if initial_source_type != "BORN_DIGITAL" else "SCANNED"
                )

                triaged_pages.append(
                    TriagedPage(
                        page_number=page_num,
                        text_source="OCR",
                        ocr_conf=ocr_result.mean_confidence,
                        lines=page_lines,
                        full_text=ocr_result.raw_text
                        or "\n".join(line.text for line in page_lines),
                        hidden_flags=hidden_flags,
                        hidden_regions=hidden_regions,
                        source_type=source_type,
                        rotation_applied=prep_meta.get("rotation_applied", 0),
                        dpi=prep_meta.get("dpi", 150),
                        is_lang_unsupported=ocr_result.is_lang_unsupported,
                        preprocessing_meta=prep_meta,
                    )
                )

        return triaged_pages
