"""Management command to seed realistic demo data for LawyerBrain local demo.

Creates:
- Firm: "Demo Law Chambers"
- Three users: admin@demo.law (ADMIN), partner@demo.law (PARTNER), associate@demo.law (ASSOCIATE)
- Cases from eval/fixtures/import/synthetic_cases_20.xlsx imported via real import service
- Partner as LEAD and Associate as MEMBER on several matters
- One hearing today and one tomorrow
- One open task for the associate
- One published client update

Idempotent: safe to run multiple times without duplicating or corrupting data.
"""

from __future__ import annotations

import hashlib
import os
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from parse.vault import VaultStorage
from workspace.import_service import (
    auto_map_headers,
    execute_import_commit,
    generate_import_preview,
    inspect_file_safety,
    parse_raw_rows,
)
from workspace.models import (
    AppUser,
    ClientUpdate,
    Hearing,
    ImportJob,
    Matter,
    MatterMember,
    Task,
    Tenant,
)

IST = ZoneInfo("Asia/Kolkata")


class Command(BaseCommand):
    help = "Seed demo data for local review (safe to run repeatedly)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("=== SEEDING DEMO DATA ==="))

        with admin_db_context():
            # 1. Firm: Demo Law Chambers
            tenant = Tenant.objects.filter(name="Demo Law Chambers").first()
            if not tenant:
                tenant_id = mint_id("ten")
                tenant = Tenant.objects.create(
                    tenant_id=tenant_id,
                    name="Demo Law Chambers",
                    deployment_mode="D2",
                    residency_policy="ANY",
                    idp={"kind": "GOOGLE", "domain": "demo.law"},
                )
                self.stdout.write(self.style.SUCCESS(f"Created tenant: Demo Law Chambers ({tenant.tenant_id})"))
            else:
                self.stdout.write(f"Existing tenant found: Demo Law Chambers ({tenant.tenant_id})")

            # 2. Three Users: admin, partner, associate
            admin_user = AppUser.objects.filter(tenant_id=tenant.tenant_id, email="admin@demo.law").first()
            if not admin_user:
                admin_user = AppUser.objects.create(
                    tenant_id=tenant.tenant_id,
                    user_id=mint_id("usr"),
                    email="admin@demo.law",
                    display_name="Demo Admin",
                    idp_subject=f"sub_demo_admin_{tenant.tenant_id}",
                    firm_role="ADMIN",
                    active=True,
                )
                self.stdout.write(self.style.SUCCESS("Created user: admin@demo.law (ADMIN)"))
            else:
                self.stdout.write("User admin@demo.law already exists.")

            partner_user = AppUser.objects.filter(tenant_id=tenant.tenant_id, email="partner@demo.law").first()
            if not partner_user:
                partner_user = AppUser.objects.create(
                    tenant_id=tenant.tenant_id,
                    user_id=mint_id("usr"),
                    email="partner@demo.law",
                    display_name="Demo Partner",
                    idp_subject=f"sub_demo_partner_{tenant.tenant_id}",
                    firm_role="PARTNER",
                    active=True,
                )
                self.stdout.write(self.style.SUCCESS("Created user: partner@demo.law (PARTNER)"))
            else:
                self.stdout.write("User partner@demo.law already exists.")

            associate_user = AppUser.objects.filter(tenant_id=tenant.tenant_id, email="associate@demo.law").first()
            if not associate_user:
                associate_user = AppUser.objects.create(
                    tenant_id=tenant.tenant_id,
                    user_id=mint_id("usr"),
                    email="associate@demo.law",
                    display_name="Demo Associate",
                    idp_subject=f"sub_demo_associate_{tenant.tenant_id}",
                    firm_role="ASSOCIATE",
                    active=True,
                )
                self.stdout.write(self.style.SUCCESS("Created user: associate@demo.law (ASSOCIATE)"))
            else:
                self.stdout.write("User associate@demo.law already exists.")

            # 3. Import cases from eval/fixtures/import/synthetic_cases_20.xlsx via real import service
            existing_matter_count = Matter.objects.filter(tenant_id=tenant.tenant_id).count()
            if existing_matter_count < 10:
                fixture_path = os.path.join(
                    str(settings.BASE_DIR),
                    "../eval/fixtures/import/synthetic_cases_20.xlsx",
                )
                if not os.path.exists(fixture_path):
                    # Check fallback location
                    fixture_path = os.path.join(
                        os.path.dirname(__file__),
                        "../../../../../eval/fixtures/import/synthetic_cases_20.xlsx",
                    )

                if not os.path.exists(fixture_path):
                    self.stdout.write(self.style.ERROR(f"Fixture file not found at: {fixture_path}"))
                    return

                with open(fixture_path, "rb") as f:
                    file_bytes = f.read()

                file_type, sheet_names, _ = inspect_file_safety(file_bytes, "synthetic_cases_20.xlsx")
                raw_sha256 = hashlib.sha256(file_bytes).hexdigest()

                storage = VaultStorage()
                client_s3 = storage._get_client()
                key = f"tpl/{tenant.tenant_id}/imports/{raw_sha256}"
                client_s3.put_object(
                    Bucket=storage.bucket_name,
                    Key=key,
                    Body=file_bytes,
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                file_ref = f"s3://{storage.bucket_name}/{key}"

                headers, raw_rows, _ = parse_raw_rows(
                    file_bytes, file_type, sheet_name=sheet_names[0] if sheet_names else None
                )
                mapping = auto_map_headers(headers)
                preview_data = generate_import_preview(tenant.tenant_id, raw_rows, mapping)

                import_id = mint_id("imj")
                ImportJob.objects.create(
                    tenant_id=tenant.tenant_id,
                    import_id=import_id,
                    filename="[DEMO] synthetic_cases_20.xlsx",
                    file_size=len(file_bytes),
                    row_count=len(raw_rows),
                    status="PREVIEW",
                    sha256=raw_sha256,
                    sheet_name=sheet_names[0] if sheet_names else None,
                    mapping=mapping,
                    client_overrides={},
                    counts=preview_data["summary"],
                    report=[],
                    file_ref=file_ref,
                    created_by=admin_user.user_id,
                    created_at=timezone.now(),
                )

                commit_result = execute_import_commit(
                    tenant_id=tenant.tenant_id,
                    importer_user_id=admin_user.user_id,
                    import_id=import_id,
                    preview_data=preview_data,
                    original_filename="synthetic_cases_20.xlsx",
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported synthetic_cases_20.xlsx: "
                        f"{commit_result['counts']['matters_created']} matters, "
                        f"{commit_result['counts']['clients_created']} clients created."
                    )
                )
            else:
                self.stdout.write(f"Tenant already has {existing_matter_count} matters imported.")

            # 4. Matter Memberships: Partner as LEAD and Associate as MEMBER on several matters
            matters = list(Matter.objects.filter(tenant_id=tenant.tenant_id).order_by("created_at", "title"))[:4]
            for m in matters:
                if not MatterMember.objects.filter(
                    tenant_id=tenant.tenant_id, matter_id=m.matter_id, user_id=partner_user.user_id
                ).exists():
                    MatterMember.objects.create(
                        tenant_id=tenant.tenant_id,
                        matter_id=m.matter_id,
                        user_id=partner_user.user_id,
                        role="LEAD",
                        granted_by=admin_user.user_id,
                    )
                if not MatterMember.objects.filter(
                    tenant_id=tenant.tenant_id, matter_id=m.matter_id, user_id=associate_user.user_id
                ).exists():
                    MatterMember.objects.create(
                        tenant_id=tenant.tenant_id,
                        matter_id=m.matter_id,
                        user_id=associate_user.user_id,
                        role="MEMBER",
                        granted_by=admin_user.user_id,
                    )
            self.stdout.write(self.style.SUCCESS(f"Assigned partner as LEAD and associate as MEMBER on {len(matters)} matters."))

            # 5. One hearing today and one tomorrow
            today_d = timezone.now().astimezone(IST).date()
            tomorrow_d = today_d + timedelta(days=1)
            mat_1 = matters[0] if matters else None
            mat_2 = matters[1] if len(matters) > 1 else mat_1

            if mat_1 and not Hearing.objects.filter(
                tenant_id=tenant.tenant_id, matter_id=mat_1.matter_id, date=today_d
            ).exists():
                Hearing.objects.create(
                    tenant_id=tenant.tenant_id,
                    matter_id=mat_1.matter_id,
                    hearing_id=mint_id("hrg"),
                    date=today_d,
                    court_no="Court 1",
                    item_no="12",
                    bench="Principal Bench",
                    purpose="[DEMO] Admission and Interim Relief Hearing",
                    source="MANUAL",
                    source_ref="[DEMO] Seeded Listing",
                    status="LISTED",
                    entered_by=partner_user.user_id,
                )
                self.stdout.write(self.style.SUCCESS(f"Created demo hearing for today ({today_d}) on '{mat_1.title}'."))

            if mat_2 and not Hearing.objects.filter(
                tenant_id=tenant.tenant_id, matter_id=mat_2.matter_id, date=tomorrow_d
            ).exists():
                Hearing.objects.create(
                    tenant_id=tenant.tenant_id,
                    matter_id=mat_2.matter_id,
                    hearing_id=mint_id("hrg"),
                    date=tomorrow_d,
                    court_no="Court 2",
                    item_no="5",
                    bench="Special Bench II",
                    purpose="[DEMO] Final Arguments and Rejoinder",
                    source="MANUAL",
                    source_ref="[DEMO] Seeded Listing",
                    status="LISTED",
                    entered_by=partner_user.user_id,
                )
                self.stdout.write(self.style.SUCCESS(f"Created demo hearing for tomorrow ({tomorrow_d}) on '{mat_2.title}'."))

            # 6. One open task for the associate
            if mat_1 and not Task.objects.filter(
                tenant_id=tenant.tenant_id, assignee=associate_user.user_id, status="OPEN"
            ).exists():
                Task.objects.create(
                    tenant_id=tenant.tenant_id,
                    task_id=mint_id("tsk"),
                    matter_id=mat_1.matter_id,
                    title="[DEMO] Prepare synopsis of arguments and list of dates",
                    notes="[DEMO] Review petition documents and prepare cross-referenced list of dates ahead of listing.",
                    assignee=associate_user.user_id,
                    due_on=today_d,
                    status="OPEN",
                    created_by=partner_user.user_id,
                )
                self.stdout.write(self.style.SUCCESS(f"Created open task for associate on '{mat_1.title}'."))

            # 7. One published client update
            if mat_1 and not ClientUpdate.objects.filter(
                tenant_id=tenant.tenant_id, matter_id=mat_1.matter_id
            ).exists():
                ClientUpdate.objects.create(
                    tenant_id=tenant.tenant_id,
                    update_id=mint_id("cup"),
                    matter_id=mat_1.matter_id,
                    text=(
                        "[DEMO] Matter listed for hearing before the Principal Bench today. "
                        "Senior arguing counsel has been briefed and will pray for ad-interim protection."
                    ),
                    facts={
                        "demo": True,
                        "status": "LISTED",
                        "date": today_d.isoformat(),
                        "last_hearing": {
                            "date": today_d.isoformat(),
                            "status": "LISTED",
                            "outcome": "Hearing in progress",
                        },
                    },
                    published_by=partner_user.user_id,
                    created_by=partner_user.user_id,
                )
                self.stdout.write(self.style.SUCCESS(f"Created published client update on '{mat_1.title}'."))

        self.stdout.write(self.style.SUCCESS("✓ Seed demo completed successfully."))
