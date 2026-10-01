"""Domain models for tenant workspace (tpl schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.8: Tenant, users, permissions, consent, audit (P7)
- docs/mvp/03_data_model_and_contracts.md §3.9: tpl.matter definition
- docs/01_master_architecture.md §5.2 (ID prefixes)
- DECISIONS.md (2026-10-01: CompositePrimaryKey, ewl prefix for ethical wall)
"""

from __future__ import annotations

from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey
from django.utils import timezone

from anchor_lib.models import DomainModel, PrefixedULIDField


class Tenant(DomainModel):
    """Tenant firm profile (tpl.tenant)."""

    tenant_id = PrefixedULIDField(prefix="ten", primary_key=True)
    name = models.TextField()
    deployment_mode = models.TextField(default="D2")
    residency_policy = models.TextField(
        default="ANY",
        choices=[
            ("IN_ONLY", "IN_ONLY"),
            ("IN_PREFERRED", "IN_PREFERRED"),
            ("ANY", "ANY"),
        ],
    )
    llm_policy = models.JSONField(default=dict, blank=True)
    idp = models.JSONField(
        default=dict, blank=True
    )  # {"kind": "GOOGLE"|"ENTRA", "tenant_or_domain": ...}
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."tenant'

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant_id})"


class AppUser(DomainModel):
    """User pre-provisioned under a tenant (tpl.app_user)."""

    pk = CompositePrimaryKey("tenant_id", "user_id")
    tenant_id = models.TextField()
    user_id = PrefixedULIDField(prefix="usr")
    email = models.TextField()
    display_name = models.TextField(null=True, blank=True)
    idp_subject = models.TextField(unique=True)
    firm_role = models.TextField(
        choices=[
            ("ADMIN", "ADMIN"),
            ("PARTNER", "PARTNER"),
            ("SENIOR_ASSOCIATE", "SENIOR_ASSOCIATE"),
            ("ASSOCIATE", "ASSOCIATE"),
            ("PARALEGAL", "PARALEGAL"),
            ("KM_LAWYER", "KM_LAWYER"),
            ("EDITOR", "EDITOR"),
        ]
    )
    active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'tpl"."app_user'

    def __str__(self) -> str:
        return f"{self.email} ({self.user_id}) - {self.firm_role}"


class Matter(DomainModel):
    """Legal matter workspace (tpl.matter)."""

    pk = CompositePrimaryKey("tenant_id", "matter_id")
    tenant_id = models.TextField()
    matter_id = PrefixedULIDField(prefix="mat")
    client_matter_no = models.TextField(null=True, blank=True)
    title = models.TextField()
    client_role = models.TextField()  # PETITIONER|RESPONDENT|...
    forum = models.JSONField(null=True, blank=True)
    jurisdiction_state = models.TextField(null=True, blank=True)
    status = models.TextField(default="ACTIVE")
    residency_policy = models.TextField(null=True, blank=True)
    walled = models.BooleanField(default=False)
    legal_hold = models.BooleanField(default=False)
    context_version = models.BigIntegerField(default=0)
    membership_version = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    @property
    def restricted(self) -> bool:
        """Alias for walled flag per 00 §4 and 08 §6."""
        return self.walled

    @restricted.setter
    def restricted(self, value: bool) -> None:
        self.walled = value

    class Meta:
        managed = False
        db_table = 'tpl"."matter'

    def __str__(self) -> str:
        return f"{self.title} ({self.matter_id})"


class MatterMember(DomainModel):
    """Matter team membership (tpl.matter_member)."""

    pk = CompositePrimaryKey("tenant_id", "matter_id", "user_id", "granted_at")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    user_id = models.TextField()
    role = models.TextField(
        choices=[
            ("LEAD", "LEAD"),
            ("MEMBER", "MEMBER"),
            ("VIEWER", "VIEWER"),
        ]
    )
    granted_by = models.TextField()
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tpl"."matter_member'


class EthicalWall(DomainModel):
    """Ethical wall on a matter (tpl.ethical_wall)."""

    pk = CompositePrimaryKey("tenant_id", "wall_id")
    tenant_id = models.TextField()
    wall_id = PrefixedULIDField(prefix="ewl")
    matter_id = models.TextField()
    basis = models.TextField()
    created_by = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."ethical_wall'


class WallExclusion(DomainModel):
    """Screened user excluded by an ethical wall (tpl.wall_exclusion)."""

    pk = CompositePrimaryKey("tenant_id", "wall_id", "user_id")
    tenant_id = models.TextField()
    wall_id = models.TextField()
    user_id = models.TextField()

    class Meta:
        managed = False
        db_table = 'tpl"."wall_exclusion'


class ActorPseudonym(DomainModel):
    """Pseudonymized actor reference for feedback and audit (tpl.actor_pseudonym)."""

    pk = CompositePrimaryKey("tenant_id", "user_id")
    tenant_id = models.TextField()
    user_id = models.TextField()
    actor_ref = PrefixedULIDField(prefix="act", unique=True)

    class Meta:
        managed = False
        db_table = 'tpl"."actor_pseudonym'


class ConsentRecord(DomainModel):
    """Consent snapshot record (tpl.consent_record)."""

    pk = CompositePrimaryKey("tenant_id", "consent_snapshot_id")
    tenant_id = models.TextField()
    consent_snapshot_id = PrefixedULIDField(prefix="cns")
    level = models.TextField(
        choices=[
            ("TENANT", "TENANT"),
            ("PRACTICE_GROUP", "PRACTICE_GROUP"),
            ("MATTER", "MATTER"),
            ("CLIENT", "CLIENT"),
            ("ACTOR", "ACTOR"),
        ]
    )
    level_ref = models.TextField(null=True, blank=True)
    flags = models.JSONField(default=dict)
    evidence = models.JSONField(default=dict)
    valid_from = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tpl"."consent_record'


class AuditEvent(DomainModel):
    """Append-only cryptographic hash-chained audit event (tpl.audit_event)."""

    pk = CompositePrimaryKey("tenant_id", "audit_id")
    tenant_id = models.TextField()
    audit_id = PrefixedULIDField(prefix="adt")
    at = models.DateTimeField(default=timezone.now)
    actor = models.TextField()
    action = models.TextField()
    object_ref = models.TextField(null=True, blank=True)
    matter_id = models.TextField(null=True, blank=True)
    decision = models.TextField(
        null=True,
        blank=True,
        choices=[("ALLOW", "ALLOW"), ("DENY", "DENY")],
    )
    detail = models.JSONField(null=True, blank=True)
    prev_hash = models.BinaryField(null=True, blank=True)
    row_hash = models.BinaryField()

    class Meta:
        managed = False
        db_table = 'tpl"."audit_event'
