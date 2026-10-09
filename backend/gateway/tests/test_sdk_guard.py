"""Architectural guard ensuring LLM provider SDKs are never imported outside backend/gateway.

Normative sources:
- AGENTS.md §6: "Every model call goes through backend/gateway with a ModelTaskContract... No direct SDK calls anywhere else."
- Session S03 Directive #10: A lint or test that fails if any module outside backend/gateway imports anthropic, openai, or google SDKs.
"""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "anthropic",
        "openai",
        "google.genai",
        "google.generativeai",
        "voyageai",
    }
)


def test_no_direct_sdk_imports_outside_gateway() -> None:
    """Walk backend python files and assert no file outside backend/gateway imports provider SDKs."""
    backend_root = Path(__file__).resolve().parent.parent.parent

    violations: list[str] = []

    for py_file in backend_root.rglob("*.py"):
        # Skip virtualenvs, hidden dirs, caches, and the gateway package itself
        rel_path = py_file.relative_to(backend_root)
        parts = rel_path.parts

        if any(p.startswith(".") for p in parts):
            continue
        if parts[0] == "gateway":
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if alias.name in FORBIDDEN_MODULES or name in (
                        "anthropic",
                        "openai",
                        "voyageai",
                    ):
                        violations.append(f"{rel_path}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_root = node.module.split(".")[0]
                    if node.module in FORBIDDEN_MODULES or mod_root in (
                        "anthropic",
                        "openai",
                        "voyageai",
                    ):
                        violations.append(f"{rel_path}:{node.lineno} imports from '{node.module}'")

    assert not violations, (
        "Direct provider SDK imports found outside backend/gateway:\n"
        + "\n".join(violations)
        + "\nAll model calls must go exclusively through backend/gateway."
    )
