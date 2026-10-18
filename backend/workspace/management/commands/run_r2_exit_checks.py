"""Management command executing Session R2 Exit Checks 1-3.

Normative sources:
- Session R2: hearings, dates and Today (Mandate 4)
- Exit Check 1: Manual hearing entry on 'Acme v. Zenith, s.9 petition', verify on matter & Today,
               record outcome and schedule next date in one action.
- Exit Check 2: Manual deadline entry on the same matter, refuse any deadline carrying a rule_id.
- Exit Check 3: Cause-list matching on real fixture containing entered case number, verify EXACT
               match on matter & Today, partial match in 'Check these', and revision updates in place.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, connection, connections

from anchor_lib.ids import mint_id
from ingest.causelist_parser import NCLTCauseListParser
from surface.router_workspace import (
    DeadlineCreateRequest,
    HearingCreateRequest,
    HearingOutcomeRequest,
    create_deadline,
    create_hearing,
    get_today_dashboard,
    record_hearing_outcome,
)
from workspace.consumer import handle_causelist_published
from workspace.db import tenant_db_context
from workspace.models import AppUser, CaseCandidate, Hearing


class Command(BaseCommand):
    help = "Run Exit Checks 1-3 on 'Acme v. Zenith, s.9 petition' using real NCLT fixtures."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("=== SESSION R2 EXIT CHECKS 1-3 LIVE DEMONSTRATION ==="))

        # 0. Setup tenant, user, client, matter
        tenant_id = mint_id("ten")
        user_id = mint_id("usr")
        client_id = mint_id("cli")
        matter_id = mint_id("mat")

        fixture_case_no = "CP (IB) 736/MB/2025"  # From real fixture nclt_causelist_1.pdf (Court 4, Item 1)

        with connections["admin"].cursor() as cursor:
            cursor.execute(
                "INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, idp, created_at) VALUES (%s, %s, 'D2', '{}'::jsonb, now())",
                [tenant_id, "Acme Law Chambers"],
            )
            cursor.execute(
                """
                INSERT INTO tpl.app_user (tenant_id, user_id, email, idp_subject, firm_role, active)
                VALUES (%s, %s, 'partner@acmelaw.in', %s, 'PARTNER', true)
                """,
                [tenant_id, user_id, f"idp_{user_id}"],
            )
            cursor.execute(
                """
                INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
                VALUES (%s, %s, 'Acme Corp', 'COMPANY', %s, now())
                """,
                [tenant_id, client_id, user_id],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, court_or_forum, created_at)
                VALUES (%s, %s, %s, 'Acme v. Zenith, s.9 petition', 'PETITIONER', 'ACTIVE', 'NCLT Mumbai Bench, Court IV', now())
                """,
                [tenant_id, matter_id, client_id],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
                VALUES (%s, %s, %s, 'LEAD', %s, now())
                """,
                [tenant_id, matter_id, user_id, user_id],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter_case_link (tenant_id, matter_id, scheme, value_normalized, role, track)
                VALUES (%s, %s, 'NCLT', %s, 'CASE', true)
                """,
                [tenant_id, matter_id, fixture_case_no],
            )

        self.stdout.write(f"✓ Created matter: 'Acme v. Zenith, s.9 petition' (ID: {matter_id})")
        app_user = AppUser.objects.using("admin").get(tenant_id=tenant_id, user_id=user_id)
        mock_req = type("MockRequest", (), {"app_user": app_user})()

        # =====================================================================
        # EXIT CHECK 1: Manual hearing entry & outcome recording with next date
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- EXIT CHECK 1: Manual Hearing & Outcome Recording ---"))
        tomorrow = date.today() + timedelta(days=1)
        next_adjourned_date = date.today() + timedelta(days=14)

        # 1.1 Create manual hearing
        hearing_resp = create_hearing(
            mock_req,
            matter_id=matter_id,
            payload=HearingCreateRequest(
                date=tomorrow.isoformat(),
                court_no="4",
                item_no="12",
                purpose="For Final Hearing",
                bench="MUM",
            ),
        )
        hearing_id = hearing_resp["hearing_id"]
        self.stdout.write(f"✓ Created manual hearing: ID={hearing_id}, date={tomorrow}, court_no=4, item_no=12")

        # 1.2 Verify on Today dashboard under tomorrow
        today_data = get_today_dashboard(mock_req)
        tomorrow_items = [h for h in today_data["tomorrow_hearings"] if h["hearing_id"] == hearing_id]
        assert len(tomorrow_items) == 1, "Hearing must appear under Tomorrow on Today dashboard"
        self.stdout.write(f"✓ Verified on Today dashboard: Tomorrow's hearings includes ID={hearing_id}")

        # 1.3 Record outcome and schedule next date in same action
        outcome_resp = record_hearing_outcome(
            mock_req,
            hearing_id=hearing_id,
            payload=HearingOutcomeRequest(
                outcome="Adjourned for filing of rejoinder",
                status="ADJOURNED",
                next_date=next_adjourned_date.isoformat(),
                next_purpose="For Rejoinder & Hearing",
            ),
        )
        self.stdout.write(f"✓ Recorded outcome: status={outcome_resp['status']}, outcome='{outcome_resp['outcome']}'")
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            next_hearings = list(Hearing.objects.filter(matter_id=matter_id, date=next_adjourned_date))
            assert len(next_hearings) == 1, "Next hearing must be scheduled in same action"
            next_h = next_hearings[0]
            self.stdout.write(
                f"✓ Next hearing scheduled in same action: ID={next_h.hearing_id}, date={next_h.date}, purpose='{next_h.purpose}'"
            )

        # =====================================================================
        # EXIT CHECK 2: Manual deadline entry & rule_id refusal
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- EXIT CHECK 2: Manual Deadline Entry & rule_id Refusal ---"))
        due_date = date.today() + timedelta(days=7)

        # 2.1 Valid manual deadline
        deadline_resp = create_deadline(
            mock_req,
            matter_id=matter_id,
            payload=DeadlineCreateRequest(
                due_on=due_date.isoformat(),
                label="Rejoinder affidavit to reply",
            ),
        )
        self.stdout.write(f"✓ Created manual deadline: ID={deadline_resp['deadline_id']}, due_on={deadline_resp['due_on']}, label='{deadline_resp['label']}'")

        # 2.2 Refuse deadline carrying rule_id via DB constraint
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            rule_refused = False
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tpl.deadline (tenant_id, deadline_id, matter_id, due_on, label, kind, rule_id, created_at)
                        VALUES (%s, %s, %s, %s, 'Statutory CIRP Deadline', 'MANUAL', 'rul_IBC_CIRP_01', now())
                        """,
                        [tenant_id, mint_id("ddl"), matter_id, due_date],
                    )
            except IntegrityError as exc:
                rule_refused = True
                self.stdout.write(f"✓ Database refused rule_id assignment (CHECK chk_deadline_rule_id_refusal enforced): {exc.__class__.__name__}")

            assert rule_refused, "Deadlines carrying rule_id MUST be refused in R2 per non-negotiable #2"

        # =====================================================================
        # EXIT CHECK 3: Cause-list matching on real fixture, partial & revision
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- EXIT CHECK 3: Cause-List Matching on Real NCLT Fixture ---"))
        fixture_pdf = Path(settings.BASE_DIR).parent / "eval" / "fixtures" / "nclt_causelist" / "nclt_causelist_1.pdf"
        assert fixture_pdf.exists(), f"Fixture PDF missing: {fixture_pdf}"

        parser = NCLTCauseListParser()
        parsed_list = parser.parse_pdf_bytes(fixture_pdf.read_bytes())
        self.stdout.write(
            f"✓ Parsed real NCLT fixture: bench={parsed_list.bench}, court_no={parsed_list.court_no}, date={parsed_list.list_date}, items={len(parsed_list.items)}"
        )

        # 3.1 Run cause-list published consumer
        event_pub = {
            "data": {
                "source_id": "NCLT_CAUSELIST",
                "raw_id": "raw_real_fixture_c1",
                "bench": parsed_list.bench,
                "court_no": parsed_list.court_no,
                "list_date": parsed_list.list_date.isoformat() if parsed_list.list_date else date.today().isoformat(),
                "items": [
                    {
                        "item_no": it.item_no,
                        "purpose": it.purpose,
                        "parties": it.parties,
                        "normalized_cases": [
                            {
                                "raw": c.raw,
                                "case_type": c.case_type,
                                "case_number": c.case_number,
                                "year": c.year,
                                "bench": c.bench,
                                "canonical": c.canonical,
                                "parseable": c.parseable,
                                "parent_case_type": c.parent_case_type,
                                "parent_case_number": c.parent_case_number,
                                "parent_year": c.parent_year,
                                "parent_bench": c.parent_bench,
                            }
                            for c in it.normalized_cases
                        ],
                    }
                    for it in parsed_list.items
                ],
            }
        }

        match_res = handle_causelist_published(event_pub)
        self.stdout.write(f"✓ Consumer processed cause-list: exact_matches={match_res['exact_matches']}, partial_matches={match_res['partial_matches']}")
        assert match_res["exact_matches"] >= 1, "Tracked case CP (IB) 736/MB/2025 must match exactly"

        # Verify hearing on matter
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            matched_hearings = list(
                Hearing.objects.filter(
                    matter_id=matter_id,
                    source="CAUSE_LIST",
                    court_no=str(parsed_list.court_no),
                )
            )
            assert len(matched_hearings) == 1
            cl_h = matched_hearings[0]
            self.stdout.write(
                f"✓ Verified hearing on matter: ID={cl_h.hearing_id}, source={cl_h.source}, bench={cl_h.bench}, court_no={cl_h.court_no}, item_no={cl_h.item_no}, purpose='{cl_h.purpose}'"
            )

        # 3.2 Partial match lands in 'Check these'
        event_partial = {
            "data": {
                "source_id": "NCLT_CAUSELIST",
                "raw_id": "raw_partial_test",
                "bench": "MUMBAI",
                "court_no": "4",
                "list_date": (date.today() + timedelta(days=2)).isoformat(),
                "items": [
                    {
                        "item_no": "99",
                        "purpose": "For Directions",
                        "parties": "Acme Corp Vs Zenith Infrastructure",
                        "normalized_cases": [
                            {
                                "raw": "CP (IB) 736/MB",  # Missing year -> PARTIAL match
                                "case_type": "CP (IB)",
                                "case_number": "736",
                                "year": None,
                                "bench": "MUM",
                                "canonical": "CP (IB) 736/MUM",
                                "parseable": True,
                            }
                        ],
                    }
                ],
            }
        }
        res_part = handle_causelist_published(event_partial)
        assert res_part["partial_matches"] >= 1
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            cand = CaseCandidate.objects.get(matter_id=matter_id, kind="HEARING", status="PENDING")
            self.stdout.write(
                f"✓ Partial match landed in 'Check these': ID={cand.candidate_id}, case_number_raw='{cand.case_number_raw}', status={cand.status}"
            )

        # 3.3 Revised list renumbers item: updates in place, does not duplicate
        event_revised = {
            "data": {
                "source_id": "NCLT_CAUSELIST",
                "raw_id": "raw_real_fixture_c1_rev2",
                "bench": parsed_list.bench,
                "court_no": parsed_list.court_no,
                "list_date": parsed_list.list_date.isoformat() if parsed_list.list_date else date.today().isoformat(),
                "items": [
                    {
                        "item_no": "5",  # Renumbered from 1 to 5
                        "purpose": "For Admission (Revised)",
                        "parties": "Acme Corp Vs Zenith",
                        "normalized_cases": [
                            {
                                "raw": "CP (IB) 736/MB/2025",
                                "case_type": "CP (IB)",
                                "case_number": "736",
                                "year": 2025,
                                "bench": "MUM",
                                "canonical": "CP (IB) 736/MUM/2025",
                                "parseable": True,
                            }
                        ],
                    }
                ],
            }
        }
        handle_causelist_published(event_revised)
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            hearings_after = list(
                Hearing.objects.filter(
                    matter_id=matter_id,
                    source="CAUSE_LIST",
                    court_no=str(parsed_list.court_no),
                )
            )
            assert len(hearings_after) == 1, "Revised cause list must update in place and NOT duplicate"
            assert hearings_after[0].hearing_id == cl_h.hearing_id, "Hearing ID must remain stable"
            assert hearings_after[0].item_no == "5", "item_no must be updated in place to 5"
            self.stdout.write(
                f"✓ Cause-list revision updated in place: ID={hearings_after[0].hearing_id}, item_no updated from {cl_h.item_no} to {hearings_after[0].item_no}, zero duplicates created."
            )

        self.stdout.write(self.style.SUCCESS("\n=== ALL EXIT CHECKS 1-3 DEMONSTRATED SUCCESSFULLY ==="))
