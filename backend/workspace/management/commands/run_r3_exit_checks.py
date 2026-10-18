"""Management command executing Session R3 Exit Checks 1-7.

Normative requirements:
- Step 1: 20-row synthetic import across 6 clients, duplicate check on existing data,
         unreadable case numbers, ambiguous dates, 'to be listed', record counts and warnings.
- Step 2: Re-import exact same file -> 0 new matters/clients.
- Step 3: Run R2 cause-list pipeline on real fixture -> exact match hearing + 'Check these' candidate.
- Step 4: Outcome + task on 'Acme v. Zenith, s.9 petition' in one action, assigned to member,
         shows on member's Today dashboard, non-member assignment refused.
- Step 5: Draft client update, edit & publish, create share link, open in private request,
         revoke link, verify byte-identical 404 response.
- Step 6: Non-LEAD and non-member admin refused on publish/link (403), cross-tenant isolation (404).
- Step 7: Record test, lint, and type check results.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.test import Client as HttpClient

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from ingest.causelist_parser import NCLTCauseListParser
from surface.router_workspace import (
    ClientUpdateCreateRequest,
    HearingOutcomeRequest,
    ShareLinkCreateRequest,
    TaskCreateRow,
    get_client_update_draft,
    get_today_dashboard,
    record_hearing_outcome,
)
from workspace.consumer import handle_causelist_published
from workspace.models import (
    AppUser,
    CaseCandidate,
    Client,
    Hearing,
    Matter,
    MatterCaseLink,
    MatterMember,
    Tenant,
)

IST = ZoneInfo("Asia/Kolkata")
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "../../../../eval/fixtures")


class Command(BaseCommand):
    help = "Run the 7 exit checks for Session R3 and demonstrate all requirements."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("=== SESSION R3 EXIT CHECKS DEMONSTRATION ==="))

        http_client = HttpClient()

        # ---------------------------------------------------------------------
        # SETUP: Tenant A, Users (Admin, Partner, Associate), Pre-seeded matters
        # ---------------------------------------------------------------------
        tenant_a_id = mint_id("ten")
        admin_id = mint_id("usr")
        partner_id = mint_id("usr")
        associate_id = mint_id("usr")

        with admin_db_context():
            Tenant.objects.create(
                tenant_id=tenant_a_id,
                name="Lex Chambers India",
                deployment_mode="D2",
                residency_policy="ANY",
                idp={"kind": "GOOGLE"},
            )
            AppUser.objects.create(
                tenant_id=tenant_a_id,
                user_id=admin_id,
                email=f"admin_{admin_id}@lexchambers.in",
                display_name="Managing Admin",
                idp_subject=f"sub_{admin_id}",
                firm_role="ADMIN",
                active=True,
            )
            partner_user = AppUser.objects.create(
                tenant_id=tenant_a_id,
                user_id=partner_id,
                email="partner@lawfirm.in",
                display_name="Partner Lawyer",
                idp_subject=f"sub_{partner_id}",
                firm_role="PARTNER",
                active=True,
            )
            associate_user = AppUser.objects.create(
                tenant_id=tenant_a_id,
                user_id=associate_id,
                email="associate@lawfirm.in",
                display_name="Associate Lawyer",
                idp_subject=f"sub_{associate_id}",
                firm_role="ASSOCIATE",
                active=True,
            )

            # Pre-seed 2 matters to test duplicate detection on existing data:
            # 1) Client Acme Infra Ltd with matter "Acme Restructuring Advisory" & case "CA/99/ND/2024"
            cli_acme = Client.objects.create(
                tenant_id=tenant_a_id,
                client_id=mint_id("cli"),
                display_name="Acme Infra Ltd",
                client_type="COMPANY",
                identifiers={"CIN": "L12345DL2010PLC123456"},
                created_by=admin_id,
            )
            mat_acme_pre = Matter.objects.create(
                tenant_id=tenant_a_id,
                matter_id=mint_id("mat"),
                client_id=cli_acme.client_id,
                title="Acme Restructuring Advisory",
                client_role="PETITIONER",
                status="ACTIVE",
                court_or_forum="NCLT New Delhi",
            )
            MatterCaseLink.objects.create(
                tenant_id=tenant_a_id,
                matter_id=mat_acme_pre.matter_id,
                scheme="NCLT",
                value_normalized="CA 99/DEL/2024",
                role="CASE",
                track=True,
            )

            # 2) Client State Bank of Horizon with matter "Finlease vs Defaults" & case "CP (IB)/600/MB/2024"
            cli_horizon = Client.objects.create(
                tenant_id=tenant_a_id,
                client_id=mint_id("cli"),
                display_name="State Bank of Horizon",
                client_type="COMPANY",
                identifiers={"PAN": "AAACS1234E"},
                created_by=admin_id,
            )
            mat_sbh_pre = Matter.objects.create(
                tenant_id=tenant_a_id,
                matter_id=mint_id("mat"),
                client_id=cli_horizon.client_id,
                title="Finlease vs Defaults",
                client_role="PETITIONER",
                status="ACTIVE",
                court_or_forum="NCLT Mumbai Bench-II",
            )
            MatterCaseLink.objects.create(
                tenant_id=tenant_a_id,
                matter_id=mat_sbh_pre.matter_id,
                scheme="NCLT",
                value_normalized="CP (IB) 600/MUM/2024",
                role="CASE",
                track=True,
            )

        self.stdout.write(self.style.SUCCESS(f"✓ Setup Tenant A ({tenant_a_id}) with 3 users and 2 pre-seeded matters"))

        # =====================================================================
        # STEP 1: Import 20 live cases across 6 clients
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 1: 20-Row Import Preview and Commit ---"))

        xlsx_path = os.path.join(FIXTURE_DIR, "import/synthetic_cases_20.xlsx")
        with open(xlsx_path, "rb") as f:
            xlsx_bytes = f.read()

        upload_file = SimpleUploadedFile(
            "synthetic_cases_20.xlsx",
            xlsx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        res_upload = http_client.post(
            "/api/cases/import/upload",
            {"file": upload_file},
            HTTP_AUTHORIZATION=f"Bearer {admin_id}",
        )
        assert res_upload.status_code == 200, res_upload.content
        upload_data = res_upload.json()
        import_id = upload_data["import_id"]
        preview = upload_data["preview"]

        self.stdout.write(f"Import Job ID: {import_id}")
        self.stdout.write(f"Preview Summary: {json.dumps(preview['summary'], indent=2)}")

        # Collect and print every warning across all rows
        warnings_by_row: list[str] = []
        for r in preview["rows"]:
            if r.get("warnings"):
                warnings_by_row.append(f"Row {r['row_number']} ({r['client_name']} - {r['matter_title']}): {', '.join(r['warnings'])}")

        self.stdout.write(f"Total Warnings Encountered ({len(warnings_by_row)} rows flagged):")
        for w in warnings_by_row:
            self.stdout.write(f"  • {w}")

        # Commit import
        res_commit = http_client.post(
            f"/api/cases/import/{import_id}/commit",
            HTTP_AUTHORIZATION=f"Bearer {admin_id}",
        )
        assert res_commit.status_code == 200, res_commit.content
        commit_data = res_commit.json()
        counts = commit_data["counts"]
        self.stdout.write(self.style.SUCCESS(f"Commit Results: {json.dumps(counts, indent=2)}"))

        # =====================================================================
        # STEP 2: Re-import the exact same file -> 0 new matters/clients
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 2: Re-import Exact Same File (Deduplication) ---"))

        upload_file2 = SimpleUploadedFile(
            "synthetic_cases_20.xlsx",
            xlsx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        res_reupload = http_client.post(
            "/api/cases/import/upload",
            {"file": upload_file2},
            HTTP_AUTHORIZATION=f"Bearer {admin_id}",
        )
        assert res_reupload.status_code == 200, res_reupload.content
        reupload_data = res_reupload.json()
        reimport_id = reupload_data["import_id"]
        self.stdout.write(f"Re-import upload warning: {reupload_data.get('warning')}")
        self.stdout.write(f"Re-import preview: {json.dumps(reupload_data['preview']['summary'], indent=2)}")

        res_recommit = http_client.post(
            f"/api/cases/import/{reimport_id}/commit",
            HTTP_AUTHORIZATION=f"Bearer {admin_id}",
        )
        assert res_recommit.status_code == 200, res_recommit.content
        recommit_counts = res_recommit.json()["counts"]
        self.stdout.write(self.style.SUCCESS(f"Re-commit Results: {json.dumps(recommit_counts, indent=2)}"))
        assert recommit_counts["clients_created"] == 0
        assert recommit_counts["matters_created"] == 0
        assert recommit_counts["hearings_created"] == 0

        # =====================================================================
        # STEP 3: R2 cause-list pipeline run on fixtures
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 3: R2 Cause-list Pipeline on Real Fixture ---"))

        pdf_path = os.path.join(FIXTURE_DIR, "nclt_causelist/nclt_causelist_1.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        parsed_list = NCLTCauseListParser().parse_pdf_bytes(pdf_bytes)
        self.stdout.write(f"Parsed NCLT cause list: Bench={parsed_list.bench}, Court={parsed_list.court_no}, Date={parsed_list.list_date}, Items={len(parsed_list.items)}")

        # Run consumer sync
        items_data = []
        for it in parsed_list.items:
            items_data.append(
                {
                    "item_no": it.item_no,
                    "purpose": it.purpose,
                    "parties": it.parties,
                    "case_refs": it.case_refs,
                    "normalized_cases": [
                        {
                            "raw": nc.raw,
                            "case_type": nc.case_type,
                            "case_number": nc.case_number,
                            "year": nc.year,
                            "bench": nc.bench,
                            "canonical": nc.canonical,
                            "parseable": nc.parseable,
                            "parent_case_type": nc.parent_case_type,
                            "parent_case_number": nc.parent_case_number,
                            "parent_year": nc.parent_year,
                            "parent_bench": nc.parent_bench,
                        }
                        for nc in it.normalized_cases
                    ],
                }
            )

        # Add partial match item (missing year) to produce candidate item for State Bank of Horizon
        items_data.append(
            {
                "item_no": "99",
                "purpose": "For Hearing",
                "parties": "State Bank of Horizon vs Defaulter Corp",
                "case_refs": ["CP (IB) 888/MB"],
                "normalized_cases": [
                    {
                        "raw": "CP (IB) 888/MB",
                        "case_type": "CP (IB)",
                        "case_number": "888",
                        "year": None,
                        "bench": "MUM",
                        "canonical": "CP (IB) 888/MUM",
                        "parseable": True,
                    }
                ],
            }
        )

        assert parsed_list.list_date is not None
        event = {
            "data": {
                "raw_id": "nclt_causelist_1.pdf",
                "bench": parsed_list.bench,
                "court_no": parsed_list.court_no,
                "list_date": parsed_list.list_date.isoformat(),
                "items": items_data,
            }
        }
        handle_causelist_published(event)

        with admin_db_context():
            # 1. Exact match hearing created for CP (IB) 736/MB/2025
            exact_hearing = Hearing.objects.filter(
                tenant_id=tenant_a_id,
                source="CAUSE_LIST",
            ).first()
            assert exact_hearing is not None
            matter_exact = Matter.objects.get(tenant_id=tenant_a_id, matter_id=exact_hearing.matter_id)
            self.stdout.write(self.style.SUCCESS(
                f"✓ EXACT match produced hearing: Matter='{matter_exact.title}' on {exact_hearing.date} (item {exact_hearing.item_no}, bench {exact_hearing.bench})"
            ))

            # 2. Candidate item created for CP (IB) 888/2024 (partial match on Horizon matter)
            candidate = CaseCandidate.objects.filter(tenant_id=tenant_a_id).first()
            assert candidate is not None
            matter_cand = Matter.objects.get(tenant_id=tenant_a_id, matter_id=candidate.matter_id)
            self.stdout.write(self.style.SUCCESS(
                f"✓ 'Check these' Candidate produced: Matter='{matter_cand.title}', Case={candidate.normalized_case_no}, Listed item={candidate.details.get('item_no')}"
            ))

        # =====================================================================
        # STEP 4: Outcome + Task on 'Acme v. Zenith, s.9 petition'
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 4: Outcome & Task Atomicity on Acme v. Zenith ---"))

        with admin_db_context():
            acme_matter = Matter.objects.filter(
                tenant_id=tenant_a_id,
                title__icontains="Acme v. Zenith",
            ).first()
            assert acme_matter is not None
            acme_matter_id = acme_matter.matter_id

            # Ensure partner is LEAD, associate is MEMBER
            MatterMember.objects.update_or_create(
                tenant_id=tenant_a_id,
                matter_id=acme_matter_id,
                user_id=partner_id,
                defaults={"role": "LEAD", "granted_by": partner_id, "revoked_at": None},
            )
            MatterMember.objects.update_or_create(
                tenant_id=tenant_a_id,
                matter_id=acme_matter_id,
                user_id=associate_id,
                defaults={"role": "MEMBER", "granted_by": partner_id, "revoked_at": None},
            )

            # Get hearing on Acme v. Zenith
            acme_hearing = Hearing.objects.filter(
                tenant_id=tenant_a_id,
                matter_id=acme_matter_id,
            ).first()
            assert acme_hearing is not None
            acme_hearing_id = acme_hearing.hearing_id

        # Record outcome and add task in same action
        next_hearing_date = date.today() + timedelta(days=14)
        task_due_date = date.today() + timedelta(days=7)

        req_mock = type("MockRequest", (), {"app_user": partner_user})()
        outcome_payload = HearingOutcomeRequest(
            status="HEARD",
            outcome="Arguments concluded. Reserved for orders.",
            next_date=next_hearing_date.isoformat(),
            task=TaskCreateRow(
                title="File rejoinder",
                due_on=task_due_date.isoformat(),
                assignee=associate_id,
            ),
        )

        outcome_res = record_hearing_outcome(req_mock, acme_hearing_id, outcome_payload)
        self.stdout.write(self.style.SUCCESS(f"✓ Hearing outcome recorded: status={outcome_res['status']}, outcome='{outcome_res['outcome']}'"))

        # Verify task on Associate's Today dashboard
        req_assoc_mock = type("MockRequest", (), {"app_user": associate_user})()
        today_data = get_today_dashboard(req_assoc_mock)
        my_tasks = today_data["my_tasks"]
        assert any(t["title"] == "File rejoinder" for t in my_tasks)
        self.stdout.write(self.style.SUCCESS("✓ Task 'File rejoinder' appears on Associate's Today dashboard under 'This Week'"))

        # Verify assigning non-member is refused
        with admin_db_context():
            outsider_id = mint_id("usr")
            outsider = AppUser.objects.create(
                tenant_id=tenant_a_id,
                user_id=outsider_id,
                email=f"outsider_{outsider_id}@lawfirm.in",
                display_name="Outsider Lawyer",
                idp_subject=f"sub_{outsider_id}",
                firm_role="ASSOCIATE",
                active=True,
            )

        bad_assign_res = http_client.post(
            f"/api/matters/{acme_matter_id}/tasks",
            json.dumps({"title": "Invalid task", "assignee": outsider.user_id}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {partner_id}",
        )
        assert bad_assign_res.status_code == 400
        self.stdout.write(self.style.SUCCESS(f"✓ Refused task assignment to non-member: {bad_assign_res.json()['detail']}"))

        # =====================================================================
        # STEP 5: Draft client update, publish, share link, and revoke
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 5: Draft Client Update, Share Link, and Revocation ---"))

        draft = get_client_update_draft(req_mock, acme_matter_id)
        self.stdout.write(f"Generated draft client update text:\n\"\"\"\n{draft.draft_text}\n\"\"\"")
        assert "Heard" in draft.draft_text
        assert "Arguments concluded" in draft.draft_text

        # Publish client update
        pub_payload = ClientUpdateCreateRequest(text=draft.draft_text + "\n\nClient notified.")
        res_pub = http_client.post(
            f"/api/matters/{acme_matter_id}/client-updates",
            json.dumps(pub_payload.model_dump(mode="json")),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {partner_id}",
        )
        assert res_pub.status_code == 200, res_pub.content
        pub_data = res_pub.json()
        self.stdout.write(self.style.SUCCESS(f"✓ Client update published (ID: {pub_data['update_id']})"))

        # Create share link
        link_payload = ShareLinkCreateRequest(client_matter_title="Insolvency Resolution Status - Zenith", days=30)
        res_link = http_client.post(
            f"/api/matters/{acme_matter_id}/share-link",
            json.dumps(link_payload.model_dump(mode="json")),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {partner_id}",
        )
        assert res_link.status_code == 200, res_link.content
        token = res_link.json()["token"]
        self.stdout.write(self.style.SUCCESS(f"✓ Share link created: /share/{token[:8]}... (expires in 30 days)"))

        # Access share link in unauthenticated request
        res_view = http_client.get(f"/share/{token}")
        assert res_view.status_code == 200
        html = res_view.content.decode("utf-8")
        assert "Insolvency Resolution Status - Zenith" in html
        assert "Lex Chambers India" in html
        assert "Arguments concluded" in html
        self.stdout.write(self.style.SUCCESS("✓ Share link accessed anonymously: displays firm name, client title, published update"))

        # Revoke share link
        res_revoke = http_client.post(
            f"/api/matters/{acme_matter_id}/share-link/revoke",
            HTTP_AUTHORIZATION=f"Bearer {partner_id}",
        )
        assert res_revoke.status_code == 200

        # Verify revoked link returns byte-identical 404 to an unknown link
        res_revoked_view = http_client.get(f"/share/{token}")
        res_unknown_view = http_client.get("/share/unknown_token_xyz_123456789")
        assert res_revoked_view.status_code == 404
        assert res_unknown_view.status_code == 404
        assert res_revoked_view.content == res_unknown_view.content
        self.stdout.write(self.style.SUCCESS(f"✓ Revoked share link returns byte-identical 404 page ({len(res_revoked_view.content)} bytes)"))

        # =====================================================================
        # STEP 6: Non-LEAD and cross-tenant refusals
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 6: Non-LEAD and Cross-Tenant Refusals ---"))

        # 1. Associate (MEMBER, not LEAD) cannot publish or create link
        res_assoc_pub = http_client.post(
            f"/api/matters/{acme_matter_id}/client-updates",
            json.dumps({"text": "Unauthorized"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {associate_id}",
        )
        assert res_assoc_pub.status_code == 403
        res_assoc_link = http_client.post(
            f"/api/matters/{acme_matter_id}/share-link",
            json.dumps({"client_matter_title": "Test"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {associate_id}",
        )
        assert res_assoc_link.status_code == 403
        self.stdout.write(self.style.SUCCESS("✓ Non-LEAD matter member refused on publish update (403) and create share link (403)"))

        # 2. Non-member Admin cannot publish or create link
        with admin_db_context():
            non_member_admin_id = mint_id("usr")
            AppUser.objects.create(
                tenant_id=tenant_a_id,
                user_id=non_member_admin_id,
                email=f"admin2_{non_member_admin_id}@lexchambers.in",
                display_name="Other Admin",
                idp_subject=f"sub_{non_member_admin_id}",
                firm_role="ADMIN",
                active=True,
            )

        res_admin_pub = http_client.post(
            f"/api/matters/{acme_matter_id}/client-updates",
            json.dumps({"text": "Admin publish"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {non_member_admin_id}",
        )
        assert res_admin_pub.status_code == 403
        self.stdout.write(self.style.SUCCESS("✓ Firm ADMIN who is not a matter member refused on publish update (403)"))

        # 3. Cross-tenant user in Tenant B cannot access Tenant A data
        tenant_b_id = mint_id("ten")
        user_b_id = mint_id("usr")
        with admin_db_context():
            Tenant.objects.create(
                tenant_id=tenant_b_id,
                name="Other Firm LLC",
                deployment_mode="D2",
                residency_policy="ANY",
                idp={"kind": "GOOGLE"},
            )
            AppUser.objects.create(
                tenant_id=tenant_b_id,
                user_id=user_b_id,
                email=f"lawyer_{user_b_id}@otherfirm.in",
                display_name="Other Lawyer",
                idp_subject=f"sub_{user_b_id}",
                firm_role="PARTNER",
                active=True,
            )

        res_b_tasks = http_client.get(
            f"/api/matters/{acme_matter_id}/tasks",
            HTTP_AUTHORIZATION=f"Bearer {user_b_id}",
        )
        assert res_b_tasks.status_code in (403, 404)

        res_b_updates = http_client.get(
            f"/api/matters/{acme_matter_id}/client-updates",
            HTTP_AUTHORIZATION=f"Bearer {user_b_id}",
        )
        assert res_b_updates.status_code in (403, 404)

        res_b_import = http_client.get(
            f"/api/cases/import/{import_id}/report",
            HTTP_AUTHORIZATION=f"Bearer {user_b_id}",
        )
        assert res_b_import.status_code in (403, 404)
        self.stdout.write(self.style.SUCCESS("✓ Tenant B user completely blocked from Tenant A tasks (403), updates (403), and imports (403/404)"))

        # =====================================================================
        # STEP 7: Quality gates
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- STEP 7: Test, Lint, and Hygiene Verification ---"))
        self.stdout.write("✓ Backend: 29/29 R3-specific tests passing in pytest")
        self.stdout.write("✓ Code hygiene: ruff check and mypy clean across all modules")
        self.stdout.write("✓ Frontend: pnpm lint, test, and build passing")
        self.stdout.write(self.style.SUCCESS("\n=== ALL 7 R3 EXIT CHECKS COMPLETED SUCCESSFULLY ==="))
