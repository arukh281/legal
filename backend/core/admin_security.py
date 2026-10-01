"""Admin security middleware restricting Django Admin in production to staff with MFA and allowed IPs.

Normative sources:
- Session S03 follow-up Directive #1: Restrict admin in prod to staff with MFA and an IP allowlist.
"""

from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

from core.db_router import admin_db_context


class AdminSecurityMiddleware:
    """Enforces production admin security guards:
    1. IP allowlist restriction.
    2. Staff and active account verification.
    3. Multi-factor authentication (MFA) verification.
    4. Routes admin execution context to 'admin' connection alias (admin_rw with BYPASSRLS).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/admin/"):
            is_prod = getattr(settings, "ENVIRONMENT", "") == "production"
            if is_prod:
                # 1. IP allowlist check
                ip_allowlist = getattr(settings, "ADMIN_IP_ALLOWLIST", [])
                if ip_allowlist:
                    remote_ip = request.META.get("HTTP_X_FORWARDED_FOR")
                    if remote_ip:
                        client_ip = remote_ip.split(",")[0].strip()
                    else:
                        client_ip = request.META.get("REMOTE_ADDR", "")
                    if client_ip not in ip_allowlist:
                        return HttpResponseForbidden(
                            f"Admin access forbidden from IP '{client_ip}'."
                        )

                # 2. MFA verification check for authenticated staff accessing admin pages
                if (
                    hasattr(request, "user")
                    and request.user.is_authenticated
                    and request.path not in ("/admin/login/", "/admin/logout/")
                ):
                    if not request.user.is_staff or not request.user.is_active:
                        return HttpResponseForbidden("Staff privileges required.")
                    mfa_verified = request.session.get("mfa_verified", False) or getattr(
                        request.user, "mfa_verified", False
                    )
                    if not mfa_verified:
                        return HttpResponseForbidden(
                            "Multi-factor authentication (MFA) verification required for admin access."
                        )

            with admin_db_context():
                return self.get_response(request)

        return self.get_response(request)
