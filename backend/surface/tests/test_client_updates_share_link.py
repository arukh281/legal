"""Unit and contract tests for Client Updates and Public Share Links (Session R3).

Normative tests:
- Client updates are immutable published snapshots (Correction 6: DB trigger prevents UPDATE/DELETE).
- Draft generation: deterministic text, facts extracted, filed by firm documents meeting Correction 17.
- Matter LEAD only may publish updates or manage share links (create, extend, revoke).
- Creating a share link revokes previous links in same transaction (Correction 18).
- Public share page:
  - Security definer function owned by share_reader; app_rw with no tenant set can call function but cannot SELECT tpl.client_update (Correction 2).
  - Output shows only published text and date; facts are dropped (Correction 3).
  - Access log in ops.share_link_access with HMAC-SHA256 hashed IP; rate limiting 30/min IP, 60/min link; identical 404 response (Correction 4).
  - Audit event SHARE_LINK_VIEW written in Python (Correction 5).
  - HTML headers: noindex, nofollow, no-referrer, no scripts.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test import Client as HttpClient
from django.utils import timezone

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace.models import (
    AppUser,
    AuditEvent,
    Client,
    ClientUpdate,
    Hearing,
    Matter,
    MatterMember,
    Pdoc,
    ShareLink,
    Tenant,
)

IST = ZoneInfo("Asia/Kolkata")
pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture(autouse=True)
def enable_dev_auth(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def r3_client_update_setup() -> dict[str, Any]:
    tenant_id = mint_id("ten")
    lead_id = mint_id("usr")
    member_id = mint_id("usr")

    with admin_db_context():
        Tenant.objects.create(
            tenant_id=tenant_id,
            name="Sterling Legal LLP",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=lead_id,
            email=f"lead_{lead_id}@firm.in",
            display_name="Lead Partner",
            idp_subject=f"sub_{lead_id}",
            firm_role="PARTNER",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=member_id,
            email=f"member_{member_id}@firm.in",
            display_name="Associate Lawyer",
            idp_subject=f"sub_{member_id}",
            firm_role="ASSOCIATE",
            active=True,
        )

        client_id = mint_id("cli")
        Client.objects.create(
            tenant_id=tenant_id,
            client_id=client_id,
            display_name="Sterling Industries",
            client_type="COMPANY",
            created_by=lead_id,
        )

        matter_id = mint_id("mat")
        Matter.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            client_id=client_id,
            title="Sterling Insolvency Resolution",
            client_role="PETITIONER",
            case_type="IBC",
            court_or_forum="NCLT Mumbai Bench-I",
            status="ACTIVE",
            walled=False,
        )

        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=lead_id, role="LEAD")
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=member_id, role="MEMBER")

        today_d = timezone.now().astimezone(IST).date()
        # Past hearing with outcome
        Hearing.objects.create(
            tenant_id=tenant_id,
            hearing_id=mint_id("hrg"),
            matter_id=matter_id,
            date=today_d - timedelta(days=2),
            court_no="1",
            item_no="24",
            purpose="Admission",
            status="HEARD",
            outcome="Interim stay granted; notice issued to respondent.",
            entered_by=lead_id,
        )
        # Next upcoming hearing
        Hearing.objects.create(
            tenant_id=tenant_id,
            hearing_id=mint_id("hrg"),
            matter_id=matter_id,
            date=today_d + timedelta(days=10),
            court_no="1",
            item_no="12",
            purpose="Final Hearing",
            status="LISTED",
            entered_by=lead_id,
        )

        # Documents filed by the firm (Correction 17)
        Pdoc.objects.create(
            tenant_id=tenant_id,
            pdoc_id=mint_id("pdoc"),
            matter_id=matter_id,
            doc_type="pdf",
            provenance="UPLOADED",
            trust_label="TENANT_CLIENT_DOC",
            privilege_class="CONFIDENTIAL",
            stage="PLEADING",
            title="Application for Interim Directions",
            created_by=lead_id,
        )
        # Opposing doc (should NOT be included in "filed by the firm")
        Pdoc.objects.create(
            tenant_id=tenant_id,
            pdoc_id=mint_id("pdoc"),
            matter_id=matter_id,
            doc_type="pdf",
            provenance="UPLOADED",
            trust_label="TENANT_OPPOSING_DOC",
            privilege_class="CONFIDENTIAL",
            stage="REPLY",
            title="Respondent Objections",
            created_by=lead_id,
        )

    return {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "member_id": member_id,
        "matter_id": matter_id,
    }


def test_client_update_draft_and_publication(r3_client_update_setup: dict[str, Any]) -> None:
    """Test deterministic draft generation and LEAD publication of immutable client update."""
    ctx = r3_client_update_setup
    client = HttpClient()

    # 1. Get draft update
    res_draft = client.get(
        f"/api/matters/{ctx['matter_id']}/client-updates/draft",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_draft.status_code == 200
    draft_data = res_draft.json()
    assert "Sterling Insolvency Resolution" in draft_data["draft_text"]
    assert "Interim stay granted" in draft_data["draft_text"]
    # Verify filed documents includes firm application, but excludes respondent doc (Correction 17)
    assert "Application for Interim Directions" in draft_data["draft_text"]
    assert "Respondent Objections" not in draft_data["draft_text"]

    # 2. Member (non-lead) attempts to publish -> 403 Forbidden
    res_mem_pub = client.post(
        f"/api/matters/{ctx['matter_id']}/client-updates",
        data={
            "text": "Published text by member",
            "facts": draft_data["facts"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['member_id']}",
    )
    assert res_mem_pub.status_code == 403

    # 3. Lead publishes update
    published_text = "Case listed today. Interim relief granted by NCLT Mumbai Bench-I."
    res_pub = client.post(
        f"/api/matters/{ctx['matter_id']}/client-updates",
        data={
            "text": published_text,
            "facts": draft_data["facts"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_pub.status_code == 200
    pub_data = res_pub.json()
    assert pub_data["update_id"].startswith("cup_")
    assert pub_data["text"] == published_text

    # Verify audit event recorded
    with admin_db_context():
        audit = AuditEvent.objects.filter(
            tenant_id=ctx["tenant_id"],
            action="CLIENT_UPDATE_PUBLISH",
            object_ref=pub_data["update_id"],
        ).first()
        assert audit is not None


def test_client_update_immutability_trigger(r3_client_update_setup: dict[str, Any]) -> None:
    """Test that tpl.client_update rows are strictly immutable via DB trigger (Correction 6)."""
    ctx = r3_client_update_setup
    update_id = mint_id("cup")

    # Insert a published update
    with admin_db_context():
        ClientUpdate.objects.create(
            tenant_id=ctx["tenant_id"],
            update_id=update_id,
            matter_id=ctx["matter_id"],
            text="Original published text",
            facts={"test": True},
            published_by=ctx["lead_id"],
            created_by=ctx["lead_id"],
        )

    with connection.cursor() as cursor:
        # UPDATE must fail (revoked privilege or immutability trigger, Correction 6)
        with pytest.raises(Exception) as excinfo:
            cursor.execute(
                "UPDATE tpl.client_update SET text = 'Modified' WHERE update_id = %s",
                [update_id],
            )
        err_msg = str(excinfo.value).lower()
        assert "immutable" in err_msg or "permission denied" in err_msg

        # DELETE must fail
        with pytest.raises(Exception) as excinfo_del:
            cursor.execute(
                "DELETE FROM tpl.client_update WHERE update_id = %s",
                [update_id],
            )
        err_del = str(excinfo_del.value).lower()
        assert "immutable" in err_del or "permission denied" in err_del


def test_share_link_lifecycle_and_auto_revocation(r3_client_update_setup: dict[str, Any]) -> None:
    """Test creating, extending, revoking share links, and auto-revocation of prior links (Correction 18)."""
    ctx = r3_client_update_setup
    client = HttpClient()

    # 1. Create first share link
    res1 = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Sterling Case Client Portal", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res1.status_code == 200
    link1_data = res1.json()
    token1 = link1_data["token"]
    assert token1 is not None
    assert len(token1) >= 32

    # 2. Create second share link -> must revoke the first link in the same transaction (Correction 18)
    res2 = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Sterling Case Client Portal v2", "days": 60},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res2.status_code == 200
    link2_data = res2.json()

    # Verify link1 is now revoked in database
    with admin_db_context():
        l1_db = ShareLink.objects.get(tenant_id=ctx["tenant_id"], link_id=link1_data["link_id"])
        assert l1_db.revoked_at is not None

        l2_db = ShareLink.objects.get(tenant_id=ctx["tenant_id"], link_id=link2_data["link_id"])
        assert l2_db.revoked_at is None

    # 3. Extend link2
    res_ext = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link/extend",
        data={"days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_ext.status_code == 200
    assert res_ext.json()["expires_at"] > link2_data["expires_at"]

    # 4. Revoke link2
    res_rev = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link/revoke",
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_rev.status_code == 200
    assert res_rev.json()["revoked_at"] is not None


def test_public_share_endpoint_security_and_rendering(r3_client_update_setup: dict[str, Any], settings: Any) -> None:
    """Test public HTML share page: security definer role isolation, rate limiting, and 404 uniformity."""
    ctx = r3_client_update_setup
    client = HttpClient()

    # 1. Publish an update
    pub_text = "NCLT bench granted stay on liquidation proceedings."
    update_id = mint_id("cup")
    with admin_db_context():
        ClientUpdate.objects.create(
            tenant_id=ctx["tenant_id"],
            update_id=update_id,
            matter_id=ctx["matter_id"],
            text=pub_text,
            facts={"internal_note": "Confidential internal fact that must NOT reach client"},
            published_by=ctx["lead_id"],
            created_by=ctx["lead_id"],
        )

    # 2. Create active share link
    res_link = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Sterling Case Status", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_link.status_code == 200
    raw_token = res_link.json()["token"]

    # 3. Test Security Definer Function Isolation (Correction 2):
    # As app_rw without tenant context, function returns row, but direct SELECT on tpl.client_update returns 0!
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    client_ip = "192.168.1.100"
    ip_hash = hmac.new(b"test_secret", client_ip.encode("utf-8"), hashlib.sha256).hexdigest()

    with connection.cursor() as cursor:
        cursor.execute("RESET app.tenant_id")
        cursor.execute("RESET app.user_id")

        cursor.execute("SELECT count(*) FROM tpl.client_update")
        count = cursor.fetchone()[0]
        assert count == 0

        cursor.execute(
            "SELECT tpl.get_public_share_update(%s, %s)",
            [token_hash, ip_hash],
        )
        data = cursor.fetchone()[0]
        assert data is not None
        assert data["client_matter_title"] == "Sterling Case Status"
        assert len(data["updates"]) > 0
        assert data["updates"][0]["text"] == pub_text

    # 4. Access public endpoint via Django HTML view
    resp_pub = client.get(f"/share/{raw_token}", REMOTE_ADDR="192.168.1.100")
    assert resp_pub.status_code == 200
    assert "text/html" in resp_pub["Content-Type"]

    # Security headers
    assert resp_pub.headers.get("X-Robots-Tag") == "noindex, nofollow"
    assert resp_pub.headers.get("Referrer-Policy") == "no-referrer"

    html_content = resp_pub.content.decode("utf-8")
    assert "Sterling Case Status" in html_content
    assert pub_text in html_content
    # Correction 3: Facts must NOT be present
    assert "Confidential internal fact" not in html_content
    # No scripts
    assert "<script" not in html_content

    # Check audit log for SHARE_LINK_VIEW (Correction 5)
    with admin_db_context():
        audit = AuditEvent.objects.filter(
            tenant_id=ctx["tenant_id"],
            action="SHARE_LINK_VIEW",
            actor="public:share_link",
        ).first()
        assert audit is not None

    # 5. Invalid token -> identical 404
    resp_bad = client.get("/share/nonexistent_token_12345", REMOTE_ADDR="192.168.1.100")
    assert resp_bad.status_code == 404
    assert "not available" in resp_bad.content.decode("utf-8").lower()


def test_uvicorn_share_token_logging_filter() -> None:
    """Session R3 Item 10: Uvicorn access log filter replaces /share/<token> with /share/<redacted>."""
    import logging

    from core.logging import UvicornShareTokenFilter

    filt = UvicornShareTokenFilter()

    # Case A: record with args tuple (standard uvicorn format)
    rec1 = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="uvicorn/protocols/http/httptools_impl.py",
        lineno=100,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("192.168.1.1:54321", "GET", "/share/secret_token_1234567890abcdef", "1.1", 200),
        exc_info=None,
    )
    filt.filter(rec1)
    assert isinstance(rec1.args, tuple)
    assert rec1.args[2] == "/share/<redacted>"
    assert rec1.getMessage() == '192.168.1.1:54321 - "GET /share/<redacted> HTTP/1.1" 200'

    # Case B: record with formatted message string
    rec2 = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='10.0.0.1 - "GET /share/secret_token_987654321?foo=bar HTTP/1.1" 200',
        args=(),
        exc_info=None,
    )
    filt.filter(rec2)
    assert "secret_token" not in rec2.msg
    assert "/share/<redacted>" in rec2.msg


def test_share_link_responses_byte_identical(r3_client_update_setup: dict[str, Any]) -> None:
    """Session R3 Item 11: An expired link, revoked link, and unknown token return byte-identical bodies."""
    ctx = r3_client_update_setup
    client = HttpClient()

    # 1. Create a share link to revoke
    res1 = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Portal 1", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    token_revoked = res1.json()["token"]
    # Revoke it
    client.post(
        f"/api/matters/{ctx['matter_id']}/share-link/revoke",
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )

    # 2. Create a share link and manually expire it
    res2 = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Portal 2", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    token_expired = res2.json()["token"]
    with admin_db_context():
        ShareLink.objects.filter(matter_id=ctx["matter_id"], link_id=res2.json()["link_id"]).update(
            expires_at=timezone.now() - timedelta(days=5)
        )

    # 3. Unknown token
    token_unknown = "shl_nonexistent_token_0123456789"

    resp_unknown = client.get(f"/share/{token_unknown}", REMOTE_ADDR="192.168.1.50")
    resp_revoked = client.get(f"/share/{token_revoked}", REMOTE_ADDR="192.168.1.51")
    resp_expired = client.get(f"/share/{token_expired}", REMOTE_ADDR="192.168.1.52")

    assert resp_unknown.status_code == 404
    assert resp_revoked.status_code == 404
    assert resp_expired.status_code == 404

    # Body bytes must be strictly identical
    assert resp_unknown.content == resp_revoked.content == resp_expired.content


def test_share_link_rate_limit_31st_view(r3_client_update_setup: dict[str, Any]) -> None:
    """Session R3 Item 11: The 31st view in a minute from one IP gets the not available 404 page."""
    ctx = r3_client_update_setup
    client = HttpClient()

    # Create active share link
    res = client.post(
        f"/api/matters/{ctx['matter_id']}/share-link",
        data={"client_matter_title": "Active Rate Limited Portal", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    token = res.json()["token"]

    test_ip = "198.51.100.42"

    # First 30 requests succeed
    for i in range(30):
        resp = client.get(f"/share/{token}", REMOTE_ADDR=test_ip)
        assert resp.status_code == 200, f"Request {i+1} failed"

    # 31st request from same IP hits the rate limit -> 404
    resp31 = client.get(f"/share/{token}", REMOTE_ADDR=test_ip)
    assert resp31.status_code == 404

    resp_unknown = client.get("/share/unknown_token_for_cmp", REMOTE_ADDR="192.168.1.99")
    # Body bytes must be strictly identical to unknown token 404 response
    assert resp31.content == resp_unknown.content


def test_cross_tenant_isolation_tasks_updates_links_imports(r3_client_update_setup: dict[str, Any]) -> None:
    """Session R3 Item 11: A user in tenant B cannot list, read or act on tenant A's tasks, updates, links or imports."""
    ctx_a = r3_client_update_setup
    client = HttpClient()

    # 1. Create Tenant B with its own Partner user
    tenant_b_id = mint_id("ten")
    user_b_id = mint_id("usr")
    with admin_db_context():
        Tenant.objects.create(
            tenant_id=tenant_b_id,
            name="Tenant B Law Chambers",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        AppUser.objects.create(
            tenant_id=tenant_b_id,
            user_id=user_b_id,
            email="lawyer@tenantb.in",
            display_name="Tenant B Lawyer",
            idp_subject=f"sub_{user_b_id}",
            firm_role="ADMIN",
            active=True,
        )

    auth_b = f"Bearer {user_b_id}"
    matter_a = ctx_a["matter_id"]

    # 2. Tasks isolation
    # List tasks for Matter A as User B -> 403
    res_list_tasks = client.get(f"/api/matters/{matter_a}/tasks", HTTP_AUTHORIZATION=auth_b)
    assert res_list_tasks.status_code in (403, 404)

    # Create task on Matter A as User B -> 403
    res_create_task = client.post(
        f"/api/matters/{matter_a}/tasks",
        data={"title": "Cross tenant task", "assignee": user_b_id},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_create_task.status_code in (400, 403, 404)

    # 3. Client updates isolation
    # Get draft for Matter A as User B -> 403
    res_draft = client.get(f"/api/matters/{matter_a}/client-updates/draft", HTTP_AUTHORIZATION=auth_b)
    assert res_draft.status_code in (403, 404)

    # List updates for Matter A as User B -> 403
    res_list_updates = client.get(f"/api/matters/{matter_a}/client-updates", HTTP_AUTHORIZATION=auth_b)
    assert res_list_updates.status_code in (403, 404)

    # Publish update on Matter A as User B -> 403
    res_pub = client.post(
        f"/api/matters/{matter_a}/client-updates",
        data={"text": "Cross-tenant update", "facts": {}},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_pub.status_code in (403, 404)

    # 4. Share links isolation
    # Get share link for Matter A as User B -> 403
    res_link = client.get(f"/api/matters/{matter_a}/share-link", HTTP_AUTHORIZATION=auth_b)
    assert res_link.status_code in (403, 404)

    # Create share link for Matter A as User B -> 403
    res_create_shl = client.post(
        f"/api/matters/{matter_a}/share-link",
        data={"client_matter_title": "Hacked Portal", "days": 30},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_create_shl.status_code in (403, 404)

    # 5. Imports isolation
    # Setup an import job in Tenant A
    import_id_a = mint_id("imj")
    with admin_db_context():
        from workspace.models import ImportJob
        ImportJob.objects.create(
            tenant_id=ctx_a["tenant_id"],
            import_id=import_id_a,
            filename="cases_a.xlsx",
            file_size=1024,
            row_count=5,
            status="PREVIEW",
            sha256="abc123sha",
            mapping={},
            client_overrides={},
            counts={},
            report=[],
            file_ref="s3://fake/cases_a.xlsx",
            created_by=ctx_a["lead_id"],
            created_at=timezone.now(),
        )

    # User B tries to preview, commit or get report for Tenant A's import job -> 404
    res_prev = client.post(
        f"/api/cases/import/{import_id_a}/preview",
        data={"mapping": {}},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_prev.status_code == 404

    res_cmt = client.post(
        f"/api/cases/import/{import_id_a}/commit",
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_cmt.status_code == 404

    res_rep = client.get(
        f"/api/cases/import/{import_id_a}/report",
        HTTP_AUTHORIZATION=auth_b,
    )
    assert res_rep.status_code == 404


def test_hearing_outcome_rules_and_client_update_facts(r3_client_update_setup: dict[str, Any]) -> None:
    """Session R3 Fix Pass 2 - Item 1: Future outcome refused, today hearing transition, no deadlines, facts ignore client."""
    from zoneinfo import ZoneInfo
    ctx = r3_client_update_setup
    client = HttpClient()
    auth_lead = f"Bearer {ctx['lead_id']}"
    today_ist = timezone.now().astimezone(ZoneInfo("Asia/Kolkata")).date()

    # 1. Setup a future hearing (+5 days) and a hearing today
    future_date = today_ist + timedelta(days=5)
    future_hrg_id = mint_id("hrg")
    today_hrg_id = mint_id("hrg")

    with admin_db_context():
        Hearing.objects.create(
            tenant_id=ctx["tenant_id"],
            matter_id=ctx["matter_id"],
            hearing_id=future_hrg_id,
            date=future_date,
            purpose="Future Final Hearing",
            source="MANUAL",
            status="LISTED",
            entered_by=ctx["lead_id"],
        )
        Hearing.objects.create(
            tenant_id=ctx["tenant_id"],
            matter_id=ctx["matter_id"],
            hearing_id=today_hrg_id,
            date=today_ist,
            purpose="Today Hearing",
            source="MANUAL",
            status="LISTED",
            entered_by=ctx["lead_id"],
        )
        # Also create a deadline to prove it never appears in the draft
        from workspace.models import Deadline
        Deadline.objects.create(
            tenant_id=ctx["tenant_id"],
            deadline_id=mint_id("ddl"),
            matter_id=ctx["matter_id"],
            label="File Rejoinder Affidavit",
            due_on=today_ist + timedelta(days=10),
            kind="MANUAL",
            lifecycle="CONFIRMED",
            owner=ctx["lead_id"],
        )

    # 2. Attempting to record HEARD on a future hearing is refused (400)
    res_fut_heard = client.post(
        f"/api/hearings/{future_hrg_id}/outcome",
        data={"status": "HEARD", "outcome": "Arguments concluded."},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_fut_heard.status_code == 400
    assert "Record what happened on or after that day" in res_fut_heard.json()["detail"]

    # Attempting to record NOT_REACHED on future hearing is also refused
    res_fut_nr = client.post(
        f"/api/hearings/{future_hrg_id}/outcome",
        data={"status": "NOT_REACHED", "outcome": "Court rose early."},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_fut_nr.status_code == 400

    # Attempting to record invalid status (e.g. LISTED) is refused
    res_fut_inv = client.post(
        f"/api/hearings/{future_hrg_id}/outcome",
        data={"status": "LISTED", "outcome": "Still listed."},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_fut_inv.status_code == 400

    # Attempting next_date <= hearing date is refused
    res_fut_date = client.post(
        f"/api/hearings/{future_hrg_id}/outcome",
        data={"status": "ADJOURNED", "outcome": "Adjourned", "next_date": (future_date - timedelta(days=1)).isoformat()},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_fut_date.status_code == 400
    assert "must be after the hearing date" in res_fut_date.json()["detail"]

    # ADJOURNED in advance on future hearing is allowed
    res_fut_adj = client.post(
        f"/api/hearings/{future_hrg_id}/outcome",
        data={"status": "ADJOURNED", "outcome": "Bench not sitting", "next_date": (future_date + timedelta(days=7)).isoformat()},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_fut_adj.status_code == 200

    # 3. Check Draft BEFORE outcome on today's hearing:
    # Today's hearing MUST show as next_hearing, NOT as recent hearing!
    res_draft_pre = client.get(
        f"/api/matters/{ctx['matter_id']}/client-updates/draft",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_draft_pre.status_code == 200
    pre_facts = res_draft_pre.json()["facts"]
    assert pre_facts["next_hearing"]["date"] == today_ist.isoformat()
    # Ensure future hearing (even though ADJOURNED) is NEVER in last_hearing
    if pre_facts["last_hearing"]:
        assert pre_facts["last_hearing"]["date"] != future_date.isoformat()

    # Verify draft has NO deadlines
    assert "File Rejoinder Affidavit" not in res_draft_pre.json()["draft_text"]
    assert "due by" not in res_draft_pre.json()["draft_text"]
    assert "deadlines" not in pre_facts

    # 4. Record outcome on TODAY's hearing (status=HEARD)
    res_today_outcome = client.post(
        f"/api/hearings/{today_hrg_id}/outcome",
        data={"status": "HEARD", "outcome": "Order pronounced in our favor."},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_today_outcome.status_code == 200

    # 5. Check Draft AFTER outcome on today's hearing:
    # Today's hearing MUST now show as last_hearing, NOT as next_hearing!
    res_draft_post = client.get(
        f"/api/matters/{ctx['matter_id']}/client-updates/draft",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_draft_post.status_code == 200
    post_facts = res_draft_post.json()["facts"]
    assert post_facts["last_hearing"]["date"] == today_ist.isoformat()
    assert "Order pronounced in our favor" in post_facts["last_hearing"]["outcome"]

    # 6. Publishing update ignores client-sent facts
    spoofed_facts = {
        "hacked_field": "injected_by_attacker",
        "last_hearing": {"outcome": "fake news"},
    }
    res_pub = client.post(
        f"/api/matters/{ctx['matter_id']}/client-updates",
        data={
            "text": "Valid lawyer status update text.",
            "facts": spoofed_facts,
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_lead,
    )
    assert res_pub.status_code == 200
    update_id = res_pub.json()["update_id"]

    with admin_db_context():
        update_obj = ClientUpdate.objects.get(tenant_id=ctx["tenant_id"], update_id=update_id)
        # Authoritative facts strictly recomputed server-side, ignoring spoofed_facts
        assert "hacked_field" not in update_obj.facts
        assert update_obj.facts["last_hearing"]["date"] == today_ist.isoformat()

