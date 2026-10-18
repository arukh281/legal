"""Domain models for tenant workspace (tpl schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.8: Tenant, users, permissions, consent, audit (P7)
- docs/mvp/03_data_model_and_contracts.md §3.9: tpl.matter definition
- docs/01_master_architecture.md §5.2 (ID prefixes)
- DECISIONS.md (2026-10-01: CompositePrimaryKey, ewl prefix for ethical wall)
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
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


class Client(DomainModel):
    """Client entity for matter grouping (tpl.client)."""

    pk = CompositePrimaryKey("tenant_id", "client_id")
    tenant_id = models.TextField()
    client_id = PrefixedULIDField(prefix="cli")
    display_name = models.TextField()
    client_type = models.TextField(
        choices=[
            ("INDIVIDUAL", "INDIVIDUAL"),
            ("COMPANY", "COMPANY"),
            ("LLP", "LLP"),
            ("PARTNERSHIP", "PARTNERSHIP"),
            ("GOVERNMENT", "GOVERNMENT"),
            ("OTHER", "OTHER"),
        ]
    )
    identifiers = models.JSONField(default=dict, blank=True)
    contact = models.JSONField(default=dict, blank=True)
    notes = models.TextField(null=True, blank=True)
    status = models.TextField(
        default="ACTIVE",
        choices=[("ACTIVE", "ACTIVE"), ("ARCHIVED", "ARCHIVED")],
    )
    created_by = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."client'

    def __str__(self) -> str:
        return f"{self.display_name} ({self.client_id})"


class Matter(DomainModel):
    """Legal matter workspace (tpl.matter)."""

    pk = CompositePrimaryKey("tenant_id", "matter_id")
    tenant_id = models.TextField()
    matter_id = PrefixedULIDField(prefix="mat")
    client_id = models.TextField(null=True, blank=True)
    client_matter_no = models.TextField(null=True, blank=True)
    title = models.TextField()
    client_role = models.TextField()  # PETITIONER|RESPONDENT|...
    case_type = models.TextField(null=True, blank=True)
    court_or_forum = models.TextField(null=True, blank=True)
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


class MatterCaseLink(DomainModel):
    """Normalized case numbers associated with a matter (tpl.matter_case_link)."""

    pk = CompositePrimaryKey("tenant_id", "matter_id", "scheme", "value_normalized")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    case_id = models.TextField(null=True, blank=True)
    scheme = models.TextField()
    value_normalized = models.TextField()
    role = models.TextField(default="CASE")
    track = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'tpl"."matter_case_link'


class Pdoc(DomainModel):
    """Private document metadata (tpl.pdoc)."""

    pk = CompositePrimaryKey("tenant_id", "pdoc_id")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    pdoc_id = PrefixedULIDField(prefix="pdoc")
    family_id = models.TextField(null=True, blank=True)
    parent_pdoc_id = models.TextField(null=True, blank=True)
    doc_type = models.TextField()
    provenance = models.TextField()
    trust_label = models.TextField(
        choices=[
            ("TENANT_CLIENT_DOC", "TENANT_CLIENT_DOC"),
            ("TENANT_OPPOSING_DOC", "TENANT_OPPOSING_DOC"),
            ("TENANT_CORRESPONDENCE", "TENANT_CORRESPONDENCE"),
            ("TENANT_WORK_PRODUCT", "TENANT_WORK_PRODUCT"),
            ("TENANT_COURT_RECORD", "TENANT_COURT_RECORD"),
        ]
    )
    privilege_class = models.TextField()
    privilege_state = models.TextField(default="SUGGESTED")
    stage = models.TextField(
        default="OTHER",
        choices=[
            ("NOTICE", "NOTICE"),
            ("PLEADING", "PLEADING"),
            ("REPLY", "REPLY"),
            ("ORDER", "ORDER"),
            ("CORRESPONDENCE", "CORRESPONDENCE"),
            ("EVIDENCE", "EVIDENCE"),
            ("DRAFT", "DRAFT"),
            ("OTHER", "OTHER"),
        ],
    )
    title = models.TextField(null=True, blank=True)
    doc_date = models.DateField(null=True, blank=True)
    received_on = models.DateField(null=True, blank=True)
    current_version = models.TextField(null=True, blank=True)
    created_by = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    tombstoned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tpl"."pdoc'

    def __str__(self) -> str:
        return f"{self.title or self.pdoc_id} ({self.pdoc_id})"


class PdocVersion(DomainModel):
    """Specific version of a private document (tpl.pdoc_version)."""

    pk = CompositePrimaryKey("tenant_id", "pdoc_id", "pver")
    tenant_id = models.TextField()
    pdoc_id = models.TextField()
    pver = models.TextField()
    raw_sha256 = models.TextField()
    storage_uri = models.TextField()
    mime = models.TextField(null=True, blank=True)
    parsed_doc_uri = models.TextField(null=True, blank=True)
    quality = models.JSONField(null=True, blank=True)
    gate = models.TextField(
        null=True,
        blank=True,
        choices=[("PASS", "PASS"), ("FLAGGED", "FLAGGED"), ("QUARANTINED", "QUARANTINED")],
    )
    pipeline_version = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."pdoc_version'


class PrivateAnchor(DomainModel):
    """Paragraph-level private anchor (tpl.private_anchor)."""

    pk = CompositePrimaryKey("tenant_id", "anchor_id")
    tenant_id = models.TextField()
    anchor_id = models.TextField()
    pdoc_id = models.TextField()
    pver = models.TextField()
    rendition = models.TextField(null=True, blank=True)
    fragment = models.TextField()
    text = models.TextField()
    text_hash = models.TextField()
    quote_prefix = models.TextField(null=True, blank=True)
    quote_suffix = models.TextField(null=True, blank=True)
    spans = models.JSONField(default=list, blank=True)
    ocr_conf = models.FloatField(null=True, blank=True)
    privilege_class = models.TextField()

    class Meta:
        managed = False
        db_table = 'tpl"."private_anchor'


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
    seq = models.BigIntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'tpl"."audit_event'


class AuditChainHead(DomainModel):
    """Current chain head for tenant audit log, enabling O(1) appends under advisory lock."""

    tenant_id = models.CharField(max_length=64, primary_key=True)
    latest_audit_id = models.CharField(max_length=64)
    latest_hash = models.BinaryField()
    seq = models.BigIntegerField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tpl"."audit_chain_head'


class Hearing(DomainModel):
    """Court hearing or listing observation (tpl.hearing)."""

    pk = CompositePrimaryKey("tenant_id", "hearing_id")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    hearing_id = PrefixedULIDField(prefix="hrg")
    case_id = models.TextField(null=True, blank=True)
    date = models.DateField()
    court_no = models.TextField(null=True, blank=True)
    item_no = models.TextField(null=True, blank=True)
    bench = models.TextField(null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    source = models.TextField(
        default="MANUAL",
        choices=[
            ("MANUAL", "MANUAL"),
            ("CAUSE_LIST", "CAUSE_LIST"),
            ("ECOURTS", "ECOURTS"),
            ("SC", "SC"),
        ],
    )
    source_ref = models.TextField(null=True, blank=True)
    status = models.TextField(
        default="LISTED",
        choices=[
            ("LISTED", "LISTED"),
            ("HEARD", "HEARD"),
            ("ADJOURNED", "ADJOURNED"),
            ("NOT_REACHED", "NOT_REACHED"),
            ("CANCELLED", "CANCELLED"),
        ],
    )
    outcome = models.TextField(null=True, blank=True)
    next_date = models.DateField(null=True, blank=True)
    entered_by = models.TextField()
    observed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."hearing'

    def __str__(self) -> str:
        return f"Hearing({self.hearing_id}, {self.date}, {self.status})"


class Deadline(DomainModel):
    """Procedural deadline or lawyer-entered date (tpl.deadline)."""

    pk = CompositePrimaryKey("tenant_id", "deadline_id")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    deadline_id = PrefixedULIDField(prefix="ddl")
    rule_id = models.TextField(null=True, blank=True)
    rule_code = models.TextField(null=True, blank=True)
    rule_version = models.TextField(null=True, blank=True)
    label = models.TextField()
    kind = models.TextField(
        choices=[
            ("LIMITATION", "LIMITATION"),
            ("STATUTORY_REPLY", "STATUTORY_REPLY"),
            ("COURT_ORDERED", "COURT_ORDERED"),
            ("COMPLIANCE", "COMPLIANCE"),
            ("INTERNAL", "INTERNAL"),
            ("MANUAL", "MANUAL"),
        ]
    )
    calendar_ref = models.JSONField(null=True, blank=True)
    trigger_event = models.JSONField(null=True, blank=True)
    computed_date = models.DateField(null=True, blank=True)
    due_on = models.DateField()
    window_kind = models.TextField(null=True, blank=True)
    hard_limit = models.DateField(null=True, blank=True)
    extendable = models.TextField(
        null=True,
        blank=True,
        choices=[
            ("NO", "NO"),
            ("CONDONABLE", "CONDONABLE"),
            ("COURT_DISCRETION", "COURT_DISCRETION"),
        ],
    )
    statutory_anchors: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    trace = models.JSONField(default=list)
    sensitivity = models.JSONField(default=list)
    interpretation_variant = models.TextField(null=True, blank=True)
    status = models.TextField(
        null=True,
        blank=True,
        choices=[
            ("CONFIRMED_INPUTS", "CONFIRMED_INPUTS"),
            ("ASSUMED_INPUTS", "ASSUMED_INPUTS"),
            ("UNCERTAIN_CALENDAR", "UNCERTAIN_CALENDAR"),
            ("CONTESTED_RULE", "CONTESTED_RULE"),
        ],
    )
    lifecycle = models.TextField(
        default="PROPOSED",
        choices=[
            ("PROPOSED", "PROPOSED"),
            ("CONFIRMED", "CONFIRMED"),
            ("DONE", "DONE"),
            ("WAIVED", "WAIVED"),
            ("MISSED", "MISSED"),
        ],
    )
    owner = models.TextField(null=True, blank=True)
    reminders = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."deadline'

    def __str__(self) -> str:
        return f"Deadline({self.deadline_id}, {self.label}, due={self.due_on}, {self.lifecycle})"


class MatterDependency(DomainModel):
    """Inverted index linking public documents/orders to matters (tpl.matter_dependency)."""

    pk = CompositePrimaryKey("tenant_id", "matter_id", "public_id", "kind")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    public_id = models.TextField()
    match_key = models.TextField()
    as_of_legal_date = models.DateField(null=True, blank=True)
    kind = models.TextField(
        choices=[
            ("OWN_CASE", "OWN_CASE"),
            ("CITED_IN_OUR_DRAFT", "CITED_IN_OUR_DRAFT"),
            ("CITED_BY_OPPONENT", "CITED_BY_OPPONENT"),
            ("IN_MEMO_FAVOURABLE", "IN_MEMO_FAVOURABLE"),
            ("IN_MEMO_ADVERSE", "IN_MEMO_ADVERSE"),
            ("GOVERNING_PROVISION", "GOVERNING_PROVISION"),
            ("WATCHED", "WATCHED"),
        ]
    )
    weight = models.FloatField(null=True, blank=True)
    source_ref = models.TextField()
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."matter_dependency'

    def __str__(self) -> str:
        return f"MatterDependency({self.matter_id}, {self.public_id}, {self.kind})"


class CaseCandidate(DomainModel):
    """Candidate hearing or order match requiring lawyer review under 'Check these' (tpl.case_candidate)."""

    pk = CompositePrimaryKey("tenant_id", "candidate_id")
    tenant_id = models.TextField()
    candidate_id = PrefixedULIDField(prefix="cnd")
    matter_id = models.TextField()
    kind = models.TextField(
        choices=[
            ("HEARING", "HEARING"),
            ("ORDER", "ORDER"),
            ("HEARING_DROPPED", "HEARING_DROPPED"),
        ]
    )
    source = models.TextField(
        choices=[
            ("CAUSE_LIST", "CAUSE_LIST"),
            ("IBBI_ORDER", "IBBI_ORDER"),
        ]
    )
    source_ref = models.TextField()
    case_number_raw = models.TextField()
    list_date = models.DateField(null=True, blank=True)
    bench = models.TextField(null=True, blank=True)
    normalized_case_no = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict)
    status = models.TextField(
        default="PENDING",
        choices=[
            ("PENDING", "PENDING"),
            ("CONFIRMED", "CONFIRMED"),
            ("DISMISSED", "DISMISSED"),
        ],
    )
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tpl"."case_candidate'

    def __str__(self) -> str:
        return f"CaseCandidate({self.candidate_id}, {self.kind}, {self.status})"

