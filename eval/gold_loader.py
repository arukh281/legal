"""Evaluation Gold Set and Case Loader.

Normative sources:
- docs/mvp/06_test_set_plan.md §1, §5, §7
- docs/mvp/03_data_model_and_contracts.md §3.15
- Session S08 Amendments 2(a) and 2(b):
  - Amendment 2(a): Rejects any case whose expected quote is not an exact substring
    of its expected anchor's live text.
  - Amendment 2(b): Agent-authored cases have provenance SYNTHETIC, reviewed=false,
    and are excluded from gating decisions until human lawyer review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.db import transaction

from anchor_lib.ids import parse_id
from core.db_router import admin_db_context
from ops.models import EvalCase, GoldSet
from parse.models import Anchor


class GoldLoaderError(Exception):
    """Raised when a gold case fails validation against corpus invariants."""


def validate_expected_quotes(case_id: str, expected: dict[str, Any]) -> None:
    """Amendment 2(a): Validate every expected quote is an exact substring of live anchor text."""
    propositions = expected.get("propositions", [])
    claims = expected.get("claims", [])
    targets = propositions + claims

    for item in targets:
        if not isinstance(item, dict):
            continue
        anchor_id = item.get("anchor_id")
        quote = item.get("quote")

        if anchor_id and quote:
            anchor = Anchor.objects.filter(anchor_id=anchor_id).first()
            if not anchor:
                raise GoldLoaderError(
                    f"Case {case_id}: Expected anchor {anchor_id} does not exist in plc.anchor."
                )
            if anchor.state != "LIVE":
                raise GoldLoaderError(
                    f"Case {case_id}: Expected anchor {anchor_id} is {anchor.state}, not LIVE."
                )
            if quote not in anchor.text:
                raise GoldLoaderError(
                    f"Case {case_id}: Expected quote is not an exact substring of live anchor {anchor_id}.\n"
                    f"  Expected quote: {quote!r}\n"
                    f"  Anchor text:    {anchor.text[:150]!r}..."
                )


def load_gold_set_from_dict(data: dict[str, Any], dry_run: bool = False) -> GoldSet:
    """Load and validate a gold set and its cases into ops.gold_set and ops.eval_case."""
    gold_set_id = data.get("gold_set_id", "")
    if not gold_set_id.startswith("gld_"):
        raise GoldLoaderError(f"Invalid gold_set_id prefix: {gold_set_id} (must start with gld_)")

    # Validate ID formatting
    try:
        parsed_id = parse_id(gold_set_id)
        if not parsed_id.ulid:
            raise GoldLoaderError(f"Malformed Crockford ULID in gold_set_id: {gold_set_id}")
    except ValueError as e:
        raise GoldLoaderError(f"Invalid gold_set_id: {e}") from e

    name = data.get("name", "")
    version = int(data.get("version", 1))
    scope = data.get("scope", "PUBLIC")
    if scope not in ("PUBLIC", "TENANT_PRIVATE"):
        raise GoldLoaderError(f"Invalid scope: {scope}")

    cases_data = data.get("cases", [])

    with admin_db_context(), transaction.atomic(using="owner"):
        gold_set, _ = GoldSet.objects.update_or_create(
            gold_set_id=gold_set_id,
            defaults={
                "name": name,
                "version": version,
                "scope": scope,
                "frozen_at": data.get("frozen_at"),
                "metadata": data.get("metadata", {}),
            },
        )

        for c in cases_data:
            case_id = c.get("eval_case_id", "")
            if not case_id.startswith("evc_"):
                raise GoldLoaderError(f"Invalid eval_case_id: {case_id} (must start with evc_)")

            # Validate Crockford ULID
            try:
                p_case_id = parse_id(case_id)
                if not p_case_id.ulid:
                    raise GoldLoaderError(f"Malformed Crockford ULID in eval_case_id: {case_id}")
            except ValueError as e:
                raise GoldLoaderError(f"Invalid eval_case_id: {e}") from e

            split = c.get("split", "DEV")
            if split not in ("DEV", "EXAM", "SENTINEL"):
                raise GoldLoaderError(f"Case {case_id}: Invalid split {split}")

            task = c.get("task", "p6.qa_synthesis@1")
            strata = c.get("strata", {})
            inp = c.get("input", {})
            expected = c.get("expected", {})
            provenance = c.get("provenance", {})

            # Amendment 2(b): Agent-authored cases have provenance SYNTHETIC, reviewed=false
            if provenance.get("source") == "SYNTHETIC" and "reviewed" not in provenance:
                provenance["reviewed"] = False

                # Amendment 2(a): Validate expected quotes strictly
                validate_expected_quotes(case_id, expected)

                EvalCase.objects.update_or_create(
                    eval_case_id=case_id,
                    defaults={
                        "gold_set": gold_set,
                        "version": int(c.get("version", 1)),
                        "split": split,
                        "task": task,
                        "strata": strata,
                        "input": inp,
                        "expected": expected,
                        "provenance": provenance,
                        "depends_on_ids": c.get("depends_on_ids", []),
                        "stale": bool(c.get("stale", False)),
                    },
                )

            if dry_run:
                transaction.set_rollback(True, using="owner")

    return gold_set


def load_gold_set_from_file(file_path: str | Path, dry_run: bool = False) -> GoldSet:
    """Load a gold set from a JSON fixture file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Gold set fixture file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return load_gold_set_from_dict(data, dry_run=dry_run)
