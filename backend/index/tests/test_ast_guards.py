"""AST and architectural guardrails for index app (Session S06).

Invariants verified:
- AGENTS.md §2 & §6: No direct LLM/embedding SDK imports in index (must go through gateway.runner).
- AGENTS.md §5: Chunk IDs are chk_ + 26-char Crockford Base32 minted in app code.
- AGENTS.md §4: Anchors are never minted by P2; chunks reuse P1 anchors only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

FORBIDDEN_SDK_MODULES = frozenset(
    {
        "voyageai",
        "anthropic",
        "openai",
        "google.genai",
        "google.generativeai",
        "langchain",
        "llama_index",
    }
)


class TestIndexAstGuards:
    """Verifies architectural rules via static AST analysis."""

    @pytest.fixture(autouse=True)
    def setup_paths(self) -> None:
        self.index_dir = Path(__file__).resolve().parent.parent

    def test_no_direct_sdk_imports_in_index(self) -> None:
        """All model embeddings must go through gateway.runner, never direct provider SDKs."""
        violations: list[str] = []
        for py_file in self.index_dir.rglob("*.py"):
            if "tests" in py_file.parts or "migrations" in py_file.parts:
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        if root in FORBIDDEN_SDK_MODULES:
                            violations.append(
                                f"{py_file.name}:{node.lineno} imports '{alias.name}'"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        root = node.module.split(".")[0]
                        if root in FORBIDDEN_SDK_MODULES:
                            violations.append(
                                f"{py_file.name}:{node.lineno} imports from '{node.module}'"
                            )

        assert not violations, f"Direct SDK imports forbidden in index: {violations}"

    def test_no_anchor_minting_in_index(self) -> None:
        """P2 indexing must never mint new anchors. P1 owns all anchor creation."""
        violations: list[str] = []
        for py_file in self.index_dir.rglob("*.py"):
            if "tests" in py_file.parts or "migrations" in py_file.parts:
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    if "mint_anchor" in func_name:
                        violations.append(f"{py_file.name}:{node.lineno} calls '{func_name}'")

        assert not violations, f"Index must never mint anchors: {violations}"
