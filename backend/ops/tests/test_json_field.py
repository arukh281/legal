"""Contract test verifying that PostgreSQL JSONField consistently returns native Python dict/list.

Normative sources:
- Session S03 follow-up Directive #6: Verify JSONField round-trips dicts and never returns strings.
"""

from __future__ import annotations

import pytest

from anchor_lib.ids import mint_id
from workspace.audit import record_audit_event
from workspace.models import AuditEvent, Tenant


@pytest.mark.django_db
def test_json_field_roundtrips_dict_natively() -> None:
    """Verify that Django models with JSONField round-trip dicts as native dicts, not strings."""
    t_id = mint_id("ten")
    payload = {
        "kind": "GOOGLE",
        "nested": {"key": "val", "count": 42},
        "tags": ["alpha", "beta", 123],
        "enabled": True,
    }

    Tenant.objects.create(
        tenant_id=t_id,
        name="JSON Test Firm",
        idp=payload,
    )

    # Re-fetch from DB
    loaded = Tenant.objects.get(tenant_id=t_id)
    assert isinstance(loaded.idp, dict), f"Expected dict, got {type(loaded.idp)}"
    assert not isinstance(loaded.idp, str), "JSONField must never return a str"
    assert loaded.idp == payload
    assert isinstance(loaded.idp["nested"], dict)
    assert loaded.idp["nested"]["count"] == 42
    assert isinstance(loaded.idp["tags"], list)


@pytest.mark.django_db
def test_audit_event_detail_json_field_roundtrips() -> None:
    """Verify AuditEvent.detail JSONField returns native dicts."""
    t_id = mint_id("ten")
    detail_data = {
        "caller": "test_runner",
        "nested_meta": {"ip": "127.0.0.1", "attempts": 3},
        "flags": [True, False],
    }

    ev = record_audit_event(
        tenant_id=t_id,
        actor="usr_json_test",
        action="TEST_JSON_ROUNDTRIP",
        detail=detail_data,
    )

    loaded = AuditEvent.objects.get(tenant_id=t_id, audit_id=ev.audit_id)
    assert isinstance(loaded.detail, dict)
    assert not isinstance(loaded.detail, str)
    assert loaded.detail == detail_data
    assert loaded.detail["nested_meta"]["attempts"] == 3
