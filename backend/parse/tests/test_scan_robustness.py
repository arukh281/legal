"""Test suite for scan robustness, deskewing, auto-rotation, and image inputs (Session S05a).

Normative reference:
- Requirement 9: Preprocessing before OCR: auto-rotate, deskew, upscale low-DPI.
- Accept image inputs (JPG, PNG, TIFF, HEIC converted) by wrapping them as single-page documents.
- Synthetic fixtures tested: rotated scan, skewed phone photo, stamped page.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from parse.preprocessor import (
    estimate_skew_angle,
    is_image_data,
    preprocess_page_image,
    wrap_image_to_pdf,
)
from parse.triage import DocumentTriager


@pytest.mark.django_db
class TestScanRobustness:
    """Verifies scan preprocessing and image format normalization."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.syn_dir = self.repo_root / "eval" / "fixtures" / "synthetic"
        self.triager = DocumentTriager()

    def test_image_format_detection_and_pdf_wrapping(self) -> None:
        png_path = self.syn_dir / "rotated_90.png"
        raw_bytes = png_path.read_bytes()

        is_img, mime = is_image_data(raw_bytes)
        assert is_img is True
        assert mime == "image/png"

        pdf_bytes, meta = wrap_image_to_pdf(raw_bytes, "image/png")
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")
        assert meta["source_type"] in ["SCANNED", "PHOTO"]
        assert meta["dpi"] >= 72

    def test_skew_estimation_detects_angle(self) -> None:
        skew_path = self.syn_dir / "skewed_photo.jpg"
        img = Image.open(skew_path)
        angle = estimate_skew_angle(img)
        # Expected around 4.0 degrees magnitude
        assert 1.0 <= abs(angle) <= 8.0

        proc_img, meta = preprocess_page_image(img)
        assert meta["deskew_angle"] != 0.0

    def test_stamped_page_processes_through_triage(self) -> None:
        stamp_path = self.syn_dir / "stamped_page.png"
        raw_bytes = stamp_path.read_bytes()

        pages = self.triager.triage_document(raw_bytes, mime_hint="image/png")
        assert len(pages) == 1
        page = pages[0]
        assert page.text_source == "OCR"
        assert len(page.lines) > 0
        assert page.ocr_conf > 0.0
