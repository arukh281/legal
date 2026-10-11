"""Contract tests for ops evaluation store models and Crockford ULID ID minting.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.15
- docs/01_master_architecture.md §5.2
- Amendment 2f: ID collision fix (iml_ for merge ledger, evr_ for eval_run).
"""

from __future__ import annotations

import pytest
from django.db import transaction

from anchor_lib.ids import mint_id, parse_id
from core.db_router import admin_db_context
from ops.models import EvalCase, EvalResult, EvalRun, GoldSet
from parse.models import IdentityMergeLedger, Work


def test_prefix_registrations_and_id_collision_fix() -> None:
    """Amendment 2f: Confirm evr_ is eval_run, and iml_ is identity_merge_ledger."""
    # Eval run
    evr_id = mint_id("evr")
    assert evr_id.startswith("evr_")
    p_evr = parse_id(evr_id)
    assert p_evr.prefix == "evr"
    assert p_evr.ulid is not None

    # Identity merge ledger
    iml_id = mint_id("iml")
    assert iml_id.startswith("iml_")
    p_iml = parse_id(iml_id)
    assert p_iml.prefix == "iml"
    assert p_iml.ulid is not None

    # Gold set, eval case, eval result
    for pfx in ("gld", "evc", "evres"):
        an_id = mint_id(pfx)
        assert an_id.startswith(f"{pfx}_")
        parsed = parse_id(an_id)
        assert parsed.prefix == pfx
        assert parsed.ulid is not None


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_eval_store_crud_and_foreign_keys(db: None) -> None:
    """Validate CRUD operations and foreign key cascading across eval store tables."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            # 1. Gold Set
            gold_set_id = mint_id("gld")
            gold_set = GoldSet.objects.create(
                gold_set_id=gold_set_id,
                name="IBC Test Gold Suite",
                version=1,
                scope="PUBLIC",
                metadata={"domain": "INSOLVENCY"},
            )
            assert gold_set.gold_set_id == gold_set_id

            # 2. Eval Case
            case_id = mint_id("evc")
            eval_case = EvalCase.objects.create(
                eval_case_id=case_id,
                gold_set=gold_set,
                version=1,
                split="DEV",
                task="p6.qa_synthesis@1",
                strata={"statute": "IBC"},
                input={"question": "Test Question?"},
                expected={"in_corpus": True, "propositions": []},
                provenance={"source": "SYNTHETIC", "reviewed": False},
                depends_on_ids=["wrk_01TEST00000000000000000000"],
            )
            assert eval_case.eval_case_id == case_id
            assert eval_case.depends_on_ids == ["wrk_01TEST00000000000000000000"]

            # 3. Eval Run
            run_id = mint_id("evr")
            eval_run = EvalRun.objects.create(
                run_id=run_id,
                gold_set=gold_set,
                candidate={"pipeline_version": "p6.qa_synthesis@1"},
                metrics={"n": 1, "passed_cases": 1},
                gate_decision="PREVIEW",
            )
            assert eval_run.run_id == run_id

            # 4. Eval Result
            result_id = mint_id("evres")
            eval_result = EvalResult.objects.create(
                result_id=result_id,
                run=eval_run,
                eval_case=eval_case,
                actual={"in_corpus": True},
                passed=True,
                score=1.0,
                reasons=["ALL_PROPOSITIONS_MATCHED"],
                gate_checks={"fabricated_anchors": 0},
            )
            assert eval_result.result_id == result_id
            assert eval_result.reasons == ["ALL_PROPOSITIONS_MATCHED"]


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_identity_merge_ledger_iml_prefix_persistence(db: None) -> None:
    """Confirm identity_merge_ledger persists with iml_ prefix in postgres."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            work1 = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="Work One",
                status="ACTIVE",
            )
            work2 = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="Work Two",
                status="ACTIVE",
            )

            from django.utils import timezone

            iml_id = mint_id("iml")
            IdentityMergeLedger.objects.create(
                event_id=iml_id,
                kind="WORK",
                op="MERGE",
                from_id=work2.work_id,
                to_id=work1.work_id,
                reason="DUPLICATE_RAW_BLOB",
                confidence=1.0,
                recorded_at=timezone.now(),
                details={"source": "test"},
            )

            fetched = IdentityMergeLedger.objects.get(event_id=iml_id)
            assert fetched.event_id.startswith("iml_")
            assert fetched.from_id == work2.work_id
            assert fetched.to_id == work1.work_id
