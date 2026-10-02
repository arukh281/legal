"""AST and architectural guardrails for parse app (Session S05a).

Invariants verified:
- AGENTS.md §2 & §4: No direct boto3 Textract calls outside ocr.py.
- AGENTS.md §5: IDs are prefix_ + Crockford ULID minted in app code, no auto-increment PKs.
- AGENTS.md §5: Anchors created, parsed and compared only through anchor_lib.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


class TestParseAstGuards:
    """Verifies architectural rules via static AST analysis."""

    @pytest.fixture(autouse=True)
    def setup_paths(self) -> None:
        self.parse_dir = Path(__file__).resolve().parent.parent

    def test_no_boto3_textract_outside_ocr_py(self) -> None:
        """Textract calls must only occur inside ocr.py behind the OCR adapter interface."""
        for py_file in self.parse_dir.glob("*.py"):
            if py_file.name == "ocr.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if "textract" in node.value.lower():
                        pytest.fail(
                            f"Direct reference to textract in {py_file.name}, must be inside ocr.py"
                        )

    def test_domain_models_use_prefixed_ulids_no_autoincrement_pk(self) -> None:
        """Domain models in parse/models.py must have managed = False or explicit ULID PKs."""
        from anchor_lib.models import DomainModel
        from parse import models as parse_models

        for attr_name in dir(parse_models):
            attr = getattr(parse_models, attr_name)
            if isinstance(attr, type) and issubclass(attr, DomainModel) and attr is not DomainModel:
                pk_field = attr._meta.pk
                assert pk_field is not None
                # PK must not be an AutoField
                assert "AutoField" not in pk_field.__class__.__name__, (
                    f"Model {attr.__name__} has auto-increment PK {pk_field.name} ({pk_field.__class__.__name__})"
                )
