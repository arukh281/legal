"""Image input normalization and scan preprocessor for OCR robustness.

Normative source:
- Session S05a Requirement 9: auto-rotate, deskew, low-DPI/faint handling,
  multi-format image ingestion (JPG, PNG, TIFF, HEIC), and script gating.
"""

from __future__ import annotations

import io
import math
from typing import Any

from PIL import Image, ImageEnhance, ImageOps


def is_image_data(data: bytes) -> tuple[bool, str]:
    """Check if byte data is an image format (JPEG, PNG, TIFF, HEIC, WEBP)."""
    if len(data) < 12:
        return False, ""
    if data[:3] == b"\xff\xd8\xff":
        return True, "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True, "image/png"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return True, "image/tiff"
    if data[4:12] in (b"ftypheic", b"ftypmif1", b"ftypmsf1", b"ftypheix", b"ftyphevc"):
        return True, "image/heic"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True, "image/webp"
    return False, ""


def open_image(image_bytes: bytes, mime_type: str = "") -> Image.Image:
    """Open image bytes into a PIL Image, supporting HEIC via pillow_heif."""
    is_img, detected_mime = is_image_data(image_bytes)
    effective_mime = detected_mime or mime_type

    if effective_mime == "image/heic" or "heic" in effective_mime.lower():
        try:
            import pillow_heif

            heif_file = pillow_heif.read_heif(image_bytes)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )
            return image
        except Exception:
            pass

    return Image.open(io.BytesIO(image_bytes))


def wrap_image_to_pdf(
    image_bytes: bytes,
    mime_hint: str = "",
) -> tuple[bytes, dict[str, Any]]:
    """Convert an image (JPG, PNG, TIFF, HEIC) to a single-page PDF.

    Returns (pdf_bytes, metadata).
    """
    img = open_image(image_bytes, mime_hint)

    # 1. EXIF orientation
    rotation_applied = 0
    exif = img.getexif()
    has_camera_make = False
    if exif:
        has_camera_make = any(k in exif for k in (271, 272))  # Make, Model
        try:
            transposed = ImageOps.exif_transpose(img)
            if transposed is not None:
                img = transposed
        except Exception:
            pass

    # 2. Convert mode to RGB for standard PDF
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # 3. Detect DPI
    dpi_info = img.info.get("dpi", (150, 150))
    dpi = int(dpi_info[0]) if isinstance(dpi_info, tuple | list) else 150
    if dpi < 72:
        dpi = 72

    # 4. Source type classification
    source_type = "PHOTO" if has_camera_make else "SCANNED"

    # 5. Export to PDF bytes
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=float(dpi))
    pdf_bytes = buf.getvalue()

    meta = {
        "source_type": source_type,
        "rotation_applied": rotation_applied,
        "dpi": dpi,
        "width": img.width,
        "height": img.height,
        "format": img.format or "UNKNOWN",
    }
    return pdf_bytes, meta


def estimate_skew_angle(image: Image.Image) -> float:
    """Estimate skew angle in degrees using projection profile variance.

    Fast heuristic over -10 to +10 degrees in 0.5-degree steps.
    """
    # Resize small for fast computation
    thumb = image.convert("L").resize((300, 400), Image.Resampling.BILINEAR)

    # Threshold
    pixels = thumb.load()
    w, h = thumb.size
    binary = []
    for y in range(h):
        row = []
        for x in range(w):
            p = pixels[x, y]  # type: ignore[index]
            val = p[0] if isinstance(p, tuple | list) else p
            row.append(1 if int(val) < 128 else 0)
        binary.append(row)

    best_angle = 0.0
    max_variance = -1.0

    for angle_tenth in range(-100, 105, 10):  # -10.0 to +10.0 in 1.0 deg steps
        angle = angle_tenth / 10.0
        # Calculate horizontal projection profile variance
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        profile = [0] * h
        for y in range(h):
            for x in range(w):
                if binary[y][x]:
                    # Rotated y
                    new_y = int((y - h / 2) * cos_a - (x - w / 2) * sin_a + h / 2)
                    if 0 <= new_y < h:
                        profile[new_y] += 1

        mean = sum(profile) / h
        variance = sum((v - mean) ** 2 for v in profile) / h
        if variance > max_variance:
            max_variance = variance
            best_angle = angle

    return best_angle


def preprocess_page_image(pil_image: Image.Image) -> tuple[Image.Image, dict[str, Any]]:
    """Preprocess page image before OCR: auto-rotate, deskew, upscale, contrast."""
    meta: dict[str, Any] = {
        "rotation_applied": 0,
        "deskew_angle": 0.0,
        "dpi": 150,
        "upscaled": False,
        "contrast_enhanced": False,
    }

    img = pil_image

    # 1. EXIF orientation
    try:
        transposed = ImageOps.exif_transpose(img)
        if transposed is not None:
            img = transposed
    except Exception:
        pass

    # 2. Low-DPI check & upscaling (target width ~1800-2400 for standard A4 OCR)
    if img.width < 1200:
        scale = 1800.0 / max(1, img.width)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        meta["upscaled"] = True
        meta["dpi"] = int(scale * 100)

    # 3. Deskew
    skew = estimate_skew_angle(img)
    if abs(skew) >= 0.5:
        img = img.rotate(-skew, expand=True, fillcolor=(255, 255, 255))
        meta["deskew_angle"] = skew

    # 4. Faint / low contrast enhancement
    gray = img.convert("L")
    stat = gray.getextrema()
    if (
        isinstance(stat, tuple)
        and len(stat) == 2
        and isinstance(stat[0], int)
        and isinstance(stat[1], int)
    ):
        if (stat[1] - stat[0]) < 120:  # narrow dynamic range
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.6)
            meta["contrast_enhanced"] = True

    return img, meta


def is_non_latin_text(text: str) -> bool:
    """Check if text contains significant Indic or non-Latin script characters.

    Unicode blocks:
    - Devanagari: U+0900 - U+097F
    - Bengali: U+0980 - U+09FF
    - Gurmukhi: U+0A00 - U+0A7F
    - Gujarati: U+0A80 - U+0AFF
    - Oriya: U+0B00 - U+0B7F
    - Tamil: U+0B80 - U+0BFF
    - Telugu: U+0C00 - U+0C7F
    - Kannada: U+0C80 - U+0CFF
    - Malayalam: U+0D00 - U+0D7F
    """
    indic_count = 0
    total_alpha = 0
    for ch in text:
        if ch.isalpha():
            total_alpha += 1
            code = ord(ch)
            if 0x0900 <= code <= 0x0D7F:
                indic_count += 1

    if total_alpha == 0:
        return False
    return (indic_count / total_alpha) > 0.20
