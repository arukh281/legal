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
from workspace.models import Tenant

if TYPE_CHECKING:
    _ModelAdmin = admin.ModelAdmin[Any]
else:
    _ModelAdmin = admin.ModelAdmin


@admin.register(Tenant)
class TenantAdmin(_ModelAdmin):
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
class AdminAppUserAdmin(_ModelAdmin):
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
class AdminMatterAdmin(_ModelAdmin):
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
