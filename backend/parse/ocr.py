"""Narrow, audited OCR adapter for scanned documents.

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.7: OCR for scanned orders
- DECISIONS.md (Session S05a): Local Tesseract adapter as primary MVP development engine;
  Textract adapter interface maintained for production; fixtures recorded to avoid live calls.
- User Directives #3, #7, #8:
  Audited calls, LINE/WORD bounding boxes, per-word/line confidence, handwriting marking,
  and lang_unsupported gating.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OcrWord:
    """Individual word box and confidence."""

    text: str
    bbox: list[float]  # [x0, y0, x1, y1] normalized to [0, 1]
    confidence: float  # 0.0 to 1.0
    text_type: str = "unknown"  # "PRINTED" | "HANDWRITING" | "unknown"


@dataclass(frozen=True, slots=True)
class OcrLine:
    """A line of text composed of words."""

    text: str
    bbox: list[float]  # [x0, y0, x1, y1] normalized to [0, 1]
    confidence: float  # 0.0 to 1.0
    words: list[OcrWord]
    text_type: str = "unknown"


@dataclass(frozen=True, slots=True)
class OcrPageResult:
    """Normalized OCR response matching ocr.page.v1 contract."""

    engine: str
    engine_version: str
    page_number: int
    lines: list[OcrLine]
    mean_confidence: float
    latency_ms: int
    cost_usd: float
    has_handwriting: bool
    is_lang_unsupported: bool = False
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OcrPageResult:
        lines: list[OcrLine] = []
        for line_data in data.get("lines", []):
            words = [
                OcrWord(
                    text=w["text"],
                    bbox=w["bbox"],
                    confidence=w["confidence"],
                    text_type=w.get("text_type", "unknown"),
                )
                for w in line_data.get("words", [])
            ]
            lines.append(
                OcrLine(
                    text=line_data["text"],
                    bbox=line_data["bbox"],
                    confidence=line_data["confidence"],
                    words=words,
                    text_type=line_data.get("text_type", "unknown"),
                )
            )
        return cls(
            engine=data["engine"],
            engine_version=data["engine_version"],
            page_number=data["page_number"],
            lines=lines,
            mean_confidence=data["mean_confidence"],
            latency_ms=data.get("latency_ms", 0),
            cost_usd=data.get("cost_usd", 0.0),
            has_handwriting=data.get("has_handwriting", False),
            is_lang_unsupported=data.get("is_lang_unsupported", False),
            raw_text=data.get("raw_text", ""),
        )


class BaseOcrEngine:
    """Base interface for OCR engines."""

    def ocr_page(self, pil_image: Image.Image, page_number: int) -> OcrPageResult:
        raise NotImplementedError


class TesseractOcrEngine(BaseOcrEngine):
    """Local Tesseract OCR engine via pytesseract."""

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        import pytesseract  # type: ignore[import-untyped]

        self.engine_name = "tesseract"
        self.cost_per_page_usd = 0.0  # Local compute

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Check binary availability and pin exact version (fail loudly if missing)
        try:
            ver = pytesseract.get_tesseract_version()
            self.engine_version = str(ver)
        except Exception as e:
            raise RuntimeError(
                f"Tesseract binary missing or unusable: {e}. "
                "Install via `brew install tesseract` or `apt-get install -y tesseract-ocr`."
            ) from e

    def ocr_page(self, pil_image: Image.Image, page_number: int) -> OcrPageResult:
        import pytesseract

        from parse.preprocessor import is_non_latin_text

        t0 = time.perf_counter()
        img_w, img_h = pil_image.size

        # Run pytesseract image_to_data
        data = pytesseract.image_to_data(
            pil_image,
            output_type=pytesseract.Output.DICT,
            config="--oem 1",
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        n_boxes = len(data["text"])
        line_groups: dict[tuple[int, int, int], list[OcrWord]] = {}

        for i in range(n_boxes):
            word_text = data["text"][i].strip()
            conf_val = float(data["conf"][i])
            if not word_text or conf_val < 0:
                continue

            left = float(data["left"][i])
            top = float(data["top"][i])
            width = float(data["width"][i])
            height = float(data["height"][i])

            x0 = round(left / img_w, 4)
            y0 = round(top / img_h, 4)
            x1 = round((left + width) / img_w, 4)
            y1 = round((top + height) / img_h, 4)
            conf = round(max(0.0, min(1.0, conf_val / 100.0)), 4)

            # Tesseract has no handwriting detection: mark as "unknown"
            word = OcrWord(
                text=word_text,
                bbox=[x0, y0, x1, y1],
                confidence=conf,
                text_type="unknown",
            )

            group_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            line_groups.setdefault(group_key, []).append(word)

        lines: list[OcrLine] = []
        all_confs: list[float] = []
        raw_text_parts: list[str] = []

        for words in line_groups.values():
            if not words:
                continue
            line_text = " ".join(w.text for w in words)
            raw_text_parts.append(line_text)
            line_conf = round(sum(w.confidence for w in words) / len(words), 4)
            all_confs.extend(w.confidence for w in words)

            line_x0 = min(w.bbox[0] for w in words)
            line_y0 = min(w.bbox[1] for w in words)
            line_x1 = max(w.bbox[2] for w in words)
            line_y1 = max(w.bbox[3] for w in words)

            lines.append(
                OcrLine(
                    text=line_text,
                    bbox=[line_x0, line_y0, line_x1, line_y1],
                    confidence=line_conf,
                    words=words,
                    text_type="unknown",
                )
            )

        mean_conf = round(sum(all_confs) / max(1, len(all_confs)), 4) if all_confs else 0.0
        full_text = "\n".join(raw_text_parts)

        # Check for non-Latin script after OCR (Directive #4)
        lang_unsupported = is_non_latin_text(full_text)

        return OcrPageResult(
            engine=self.engine_name,
            engine_version=self.engine_version,
            page_number=page_number,
            lines=lines,
            mean_confidence=mean_conf,
            latency_ms=latency_ms,
            cost_usd=self.cost_per_page_usd,
            has_handwriting=False,  # Tesseract does not detect handwriting
            is_lang_unsupported=lang_unsupported,
            raw_text=full_text,
        )


class OcrAdapter:
    """Gated, audited OCR client with fixture replay and caching."""

    def __init__(
        self,
        engine: BaseOcrEngine | None = None,
        fixture_dir: Path | None = None,
    ) -> None:
        self.engine = engine or TesseractOcrEngine()
        self.fixture_dir = fixture_dir or (
            Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "ocr"
        )
        self.fixture_dir.mkdir(parents=True, exist_ok=True)

    def _fixture_path(self, raw_id: str, page_number: int) -> Path:
        safe_raw = raw_id.replace(":", "_").replace("/", "_")
        return self.fixture_dir / f"{safe_raw}_p{page_number}.json"

    def has_recorded_fixture(self, raw_id: str, page_number: int) -> bool:
        return self._fixture_path(raw_id, page_number).exists()

    def load_fixture(self, raw_id: str, page_number: int) -> OcrPageResult | None:
        path = self._fixture_path(raw_id, page_number)
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    return OcrPageResult.from_dict(data)
            except Exception as e:
                logger.warning("failed_loading_ocr_fixture", path=str(path), error=str(e))
        return None

    def save_fixture(self, raw_id: str, page_number: int, result: OcrPageResult) -> None:
        path = self._fixture_path(raw_id, page_number)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning("failed_saving_ocr_fixture", path=str(path), error=str(e))

    def process_page(
        self,
        pil_image: Image.Image,
        page_number: int,
        raw_id: str = "",
        use_cache: bool = True,
    ) -> OcrPageResult:
        """Run OCR on a page with fixture cache replay."""
        # 1. Check fixture cache
        if use_cache and raw_id:
            cached = self.load_fixture(raw_id, page_number)
            if cached is not None:
                logger.info("ocr_cache_hit", raw_id=raw_id, page=page_number)
                return cached

        # 2. Run engine OCR
        result = self.engine.ocr_page(pil_image, page_number)

        # 3. Save to fixture cache if raw_id is provided
        if raw_id:
            self.save_fixture(raw_id, page_number, result)

        logger.info(
            "ocr_page_completed",
            engine=result.engine,
            page=page_number,
            mean_conf=result.mean_confidence,
            lines=len(result.lines),
            latency_ms=result.latency_ms,
        )
        return result
