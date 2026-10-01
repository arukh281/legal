"""Django Admin configuration for workspace models.

Provides admin interfaces for Tenant, AppUser, and Matter.
Because Django 5.2's contrib.admin does not yet support models with CompositePrimaryKey directly,
AdminAppUser and AdminMatter provide clean admin interfaces mapped to tpl.app_user and tpl.matter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.db import models
from django.utils import timezone

from anchor_lib.models import PrefixedULIDField
from core.db_router import admin_db_context
from workspace.audit import record_audit_event
from workspace.models import Tenant

if TYPE_CHECKING:
    _ModelAdmin = admin.ModelAdmin[Any]
else:
    _ModelAdmin = admin.ModelAdmin


class AuditedModelAdmin(_ModelAdmin):
    """ModelAdmin that audits every admin write (create, update, delete) to the audit log."""

    def get_queryset(self, request: Any) -> Any:
        with admin_db_context():
            return super().get_queryset(request).using("admin")

    def save_model(self, request: Any, obj: Any, form: Any, change: bool) -> None:
        with admin_db_context():
            super().save_model(request, obj, form, change)
            tenant_id = getattr(obj, "tenant_id", None)
            if tenant_id:
                action = "ADMIN_UPDATE" if change else "ADMIN_CREATE"
                actor = getattr(request.user, "username", "admin_user") or "admin_user"
                record_audit_event(
                    tenant_id=tenant_id,
                    actor=actor,
                    action=action,
                    object_ref=f"{obj._meta.db_table}:{obj.pk}",
                    detail={
                        "admin_user": actor,
                        "remote_ip": request.META.get("REMOTE_ADDR"),
                        "changed_fields": list(form.changed_data) if form and hasattr(form, "changed_data") else [],
                    },
                    using="admin",
                )

    def delete_model(self, request: Any, obj: Any) -> None:
        with admin_db_context():
            tenant_id = getattr(obj, "tenant_id", None)
            if tenant_id:
                actor = getattr(request.user, "username", "admin_user") or "admin_user"
                record_audit_event(
                    tenant_id=tenant_id,
                    actor=actor,
                    action="ADMIN_DELETE",
                    object_ref=f"{obj._meta.db_table}:{obj.pk}",
                    detail={
                        "admin_user": actor,
                        "remote_ip": request.META.get("REMOTE_ADDR"),
                    },
                    using="admin",
                )
            super().delete_model(request, obj)


@admin.register(Tenant)
class TenantAdmin(AuditedModelAdmin):
    list_display = ("tenant_id", "name", "deployment_mode", "residency_policy", "created_at")
    search_fields = ("name", "tenant_id")
    readonly_fields = ("created_at",)


class AdminAppUser(models.Model):
    """Admin representation for tpl.app_user."""

    tenant_id = models.CharField(max_length=64)
    user_id = PrefixedULIDField(prefix="usr", primary_key=True)
    email = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    idp_subject = models.CharField(max_length=255, unique=True)
    firm_role = models.CharField(
        max_length=32,
        choices=[
            ("ADMIN", "ADMIN"),
            ("PARTNER", "PARTNER"),
            ("SENIOR_ASSOCIATE", "SENIOR_ASSOCIATE"),
            ("ASSOCIATE", "ASSOCIATE"),
            ("PARALEGAL", "PARALEGAL"),
            ("KM_LAWYER", "KM_LAWYER"),
            ("EDITOR", "EDITOR"),
        ],
    )
    active = models.BooleanField(default=True)

    class Meta:
        managed = False
        app_label = "workspace"
        db_table = 'tpl"."app_user'
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.email} ({self.user_id})"


@admin.register(AdminAppUser)
class AdminAppUserAdmin(AuditedModelAdmin):
    list_display = ("user_id", "email", "display_name", "firm_role", "tenant_id", "active")
    search_fields = ("email", "user_id", "display_name")
    list_filter = ("firm_role", "active")


class AdminMatter(models.Model):
    """Admin representation for tpl.matter."""

    tenant_id = models.CharField(max_length=64)
    matter_id = PrefixedULIDField(prefix="mat", primary_key=True)
    client_matter_no = models.CharField(max_length=64, null=True, blank=True)
    title = models.CharField(max_length=255)
    client_role = models.CharField(
        max_length=32,
        choices=[
            ("PETITIONER", "PETITIONER"),
            ("RESPONDENT", "RESPONDENT"),
            ("APPELLANT", "APPELLANT"),
            ("PLAINTIFF", "PLAINTIFF"),
            ("DEFENDANT", "DEFENDANT"),
            ("APPLICANT", "APPLICANT"),
            ("NOTICEE", "NOTICEE"),
            ("ADVISORY", "ADVISORY"),
            ("OTHER", "OTHER"),
        ],
    )
    forum = models.JSONField(null=True, blank=True, default=dict)
    jurisdiction_state = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=32, default="ACTIVE")
    residency_policy = models.CharField(max_length=32, null=True, blank=True)
    walled = models.BooleanField(default=False)
    legal_hold = models.BooleanField(default=False)
    context_version = models.BigIntegerField(default=0)
    membership_version = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        app_label = "workspace"
        db_table = 'tpl"."matter'
        verbose_name = "Matter"
        verbose_name_plural = "Matters"

    def __str__(self) -> str:
        return f"{self.title} ({self.matter_id})"


@admin.register(AdminMatter)
class AdminMatterAdmin(AuditedModelAdmin):
    list_display = (
        "matter_id",
        "title",
        "client_role",
        "status",
        "walled",
        "tenant_id",
        "created_at",
    )
    search_fields = ("title", "matter_id", "client_matter_no")
    list_filter = ("status", "walled", "client_role")
    readonly_fields = ("created_at",)
