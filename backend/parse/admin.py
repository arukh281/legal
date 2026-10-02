"""Django admin configuration for parse runs, review queue, and anchors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.utils.html import format_html

from parse.models import Anchor, Court, LegalCase, ParseRun, Work

if TYPE_CHECKING:
    _ModelAdmin = admin.ModelAdmin[Any]
else:
    _ModelAdmin = admin.ModelAdmin


@admin.register(ParseRun)
class ParseRunAdmin(_ModelAdmin):
    list_display = (
        "parse_id",
        "work_id",
        "doc_type",
        "gate_badge",
        "ocr_confidence",
        "hidden_flags",
        "created_at",
    )
    list_filter = ("gate", "doc_type", "created_at")
    search_fields = ("parse_id", "work__work_id", "work__title")
    readonly_fields = (
        "parse_id",
        "raw_ids",
        "manifestation",
        "work",
        "expression_key",
        "doc_type",
        "parsed_doc_uri",
        "parsed_doc_sha256",
        "quality",
        "gate",
        "anchor_changes",
        "supersedes_parse_id",
        "rights_class",
        "provenance_tier",
        "pipeline_version",
        "cost_usd",
        "created_at",
    )

    def gate_badge(self, obj: ParseRun) -> Any:
        colors = {
            "PASS": "green",
            "FLAGGED": "orange",
            "QUARANTINED": "red",
        }
        color = colors.get(obj.gate, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.gate,
        )

    gate_badge.short_description = "Gate"  # type: ignore[attr-defined]

    def ocr_confidence(self, obj: ParseRun) -> Any:
        q = obj.quality or {}
        conf = q.get("ocr_conf", 1.0)
        return f"{conf:.2%}"

    ocr_confidence.short_description = "OCR Conf"  # type: ignore[attr-defined]

    def hidden_flags(self, obj: ParseRun) -> Any:
        q = obj.quality or {}
        flags = q.get("hidden_text_flags", [])
        return ", ".join(flags) if flags else "-"

    hidden_flags.short_description = "Hidden Flags"  # type: ignore[attr-defined]


@admin.register(Court)
class CourtAdmin(_ModelAdmin):
    list_display = ("court_id", "level", "territory")
    list_filter = ("level",)
    search_fields = ("court_id",)


@admin.register(Work)
class WorkAdmin(_ModelAdmin):
    list_display = ("work_id", "work_type", "status", "court", "decision_date", "title")
    list_filter = ("work_type", "status", "court")
    search_fields = ("work_id", "title")


@admin.register(LegalCase)
class LegalCaseAdmin(_ModelAdmin):
    list_display = ("case_id", "court", "case_type", "number", "year", "cnr")
    list_filter = ("court", "case_type")
    search_fields = ("case_id", "number", "cnr")


@admin.register(Anchor)
class AnchorAdmin(_ModelAdmin):
    list_display = ("anchor_id", "work", "fragment", "number_as_printed", "ocr_conf", "state")
    list_filter = ("state", "node_type")
    search_fields = ("anchor_id", "text")
    readonly_fields = ("anchor_id", "text_hash", "first_parse_id", "last_parse_id")
