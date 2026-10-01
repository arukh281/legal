"""Architectural guard ensuring HTTP network libraries are never imported outside core/http_client.

Normative source:
- Session S04 Directive #1: HTTP guard must be repo-wide, not just ingest/.
  Only core/http_client.py may import httpx, requests, urllib.request or aiohttp
  (plus gateway adapters for LLM SDKs and storage for boto3).
  The raw transport must be private and only obtainable through GatedHttpClient.
"""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_HTTP_MODULES: frozenset[str] = frozenset(
    {
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
    }
)


def test_no_direct_http_imports_outside_core_http_client() -> None:
    """Walk all backend python files and assert no file outside core/http_client imports HTTP libraries."""
    backend_root = Path(__file__).resolve().parent.parent.parent

    violations: list[str] = []
    raw_transport_violations: list[str] = []

    for py_file in backend_root.rglob("*.py"):
        rel_path = py_file.relative_to(backend_root)
        parts = rel_path.parts

        # Skip virtualenvs, hidden dirs, caches
        if any(p.startswith(".") for p in parts):
            continue

        # Allowed exceptions for HTTP client imports:
        # 1. core/http_client.py (the designated raw transport module)
        if rel_path == Path("core/http_client.py"):
            continue
        # 2. gateway (LLM SDK adapters use their respective provider clients)
        if parts[0] == "gateway":
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception:
            continue

        for node in ast.walk(tree):
            # Check forbidden HTTP module imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    if alias.name in FORBIDDEN_HTTP_MODULES or root_name in (
                        "requests",
                        "httpx",
                        "aiohttp",
                    ):
                        violations.append(f"{rel_path}:{node.lineno} imports '{alias.name}'")
                    if alias.name.startswith("urllib.request"):
                        violations.append(f"{rel_path}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".")[0]
                    if node.module in FORBIDDEN_HTTP_MODULES or root_name in (
                        "requests",
                        "httpx",
                        "aiohttp",
                    ):
                        violations.append(f"{rel_path}:{node.lineno} imports from '{node.module}'")
                    if node.module == "urllib" or node.module.startswith("urllib.request"):
                        for alias in node.names:
                            if alias.name == "request":
                                violations.append(
                                    f"{rel_path}:{node.lineno} imports 'request' from urllib"
                                )

            # Check that RawHttpClient is never imported outside ingest/gate.py or tests
            if isinstance(node, ast.ImportFrom):
                if node.module in ("core.http_client", "backend.core.http_client"):
                    for alias in node.names:
                        if alias.name == "RawHttpClient":
                            if rel_path != Path("ingest/gate.py") and "test" not in str(rel_path):
                                raw_transport_violations.append(
                                    f"{rel_path}:{node.lineno} imports RawHttpClient directly"
                                )

    assert not violations, (
        "Direct HTTP library imports found outside core/http_client.py:\n"
        + "\n".join(violations)
        + "\nAll network requests must go exclusively through GatedHttpClient."
    )

    assert not raw_transport_violations, (
        "Direct RawHttpClient imports found outside ingest/gate.py:\n"
        + "\n".join(raw_transport_violations)
        + "\nRawHttpClient is private; all network access must go through GatedHttpClient."
    )
