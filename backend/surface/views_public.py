"""Public share link view.

Normative sources:
- Session R3 specification & review approvals:
  1. Calls tpl.get_public_share_update(token_hash, ip_hash) owned by share_reader.
  2. HMAC-SHA256 IP hashing using server SECRET_KEY.
  3. REMOTE_ADDR extraction with TRUSTED_PROXY_COUNT protection.
  4. Identical 404 response for unknown, expired, revoked, or rate-limited links.
  5. Immutable snapshot rendering: firm name, client matter title, updates newest first.
  6. Security headers: noindex, nofollow, no-referrer, CSP script-src 'none'.
  7. Auditing: records SHARE_LINK_VIEW with actor 'public:share_link' and keyed IP hash.
"""

from __future__ import annotations

import hashlib
import hmac
import html
from typing import Any

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

from workspace.audit import record_audit_event


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP securely honoring TRUSTED_PROXY_COUNT without trusting raw X-Forwarded-For."""
    trusted_proxy_count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    if trusted_proxy_count > 0:
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            proxies = [p.strip() for p in x_forwarded.split(",")]
            if len(proxies) >= trusted_proxy_count:
                return str(proxies[-trusted_proxy_count])
    remote_addr = request.META.get("REMOTE_ADDR")
    return str(remote_addr) if remote_addr else "127.0.0.1"


def compute_ip_hmac(ip: str) -> str:
    """Compute keyed HMAC-SHA256 of IP address using Django SECRET_KEY."""
    secret = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secret, ip.encode("utf-8"), hashlib.sha256).hexdigest()


NOT_AVAILABLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Case Status Not Available</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #f8fafc;
      color: #334155;
      margin: 0;
      padding: 40px 20px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 80vh;
    }
    .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 32px;
      max-width: 480px;
      width: 100%;
      text-align: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    h1 { font-size: 20px; font-weight: 600; color: #0f172a; margin-bottom: 12px; }
    p { font-size: 14px; line-height: 1.5; color: #64748b; margin: 0; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Case status not available</h1>
    <p>This update link is invalid, has expired, or has been revoked by the law firm. Please contact your legal counsel for current case information.</p>
  </div>
</body>
</html>"""


def public_share_view(request: HttpRequest, token: str) -> HttpResponse:
    """Render read-only published client updates via security definer function."""
    # Redact token from request logging
    request.path_info = "/share/<redacted>"
    request.path = "/share/<redacted>"

    ip = get_client_ip(request)
    ip_hash = compute_ip_hmac(ip)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    data: dict[str, Any] | None = None
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tpl.get_public_share_update(%s, %s)",
            [token_hash, ip_hash],
        )
        row = cursor.fetchone()
        if row and row[0]:
            data = row[0]

    # Identical generic 404 response if missing, revoked, expired, or rate-limited
    if not data or data.get("error") == "RATE_LIMITED":
        resp = HttpResponse(NOT_AVAILABLE_HTML, status=404, content_type="text/html; charset=utf-8")
        resp["X-Robots-Tag"] = "noindex, nofollow"
        resp["Referrer-Policy"] = "no-referrer"
        resp["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'none';"
        return resp

    tenant_id = data.get("tenant_id")
    link_id = data.get("link_id")
    firm_name = data.get("firm_name") or "Law Firm"
    matter_title = data.get("client_matter_title") or "Matter Updates"
    updates = data.get("updates", [])

    # Record view audit event in Python hash chain
    if tenant_id and link_id:
        record_audit_event(
            tenant_id=tenant_id,
            actor="public:share_link",
            action="SHARE_LINK_VIEW",
            object_ref=link_id,
            decision="ALLOW",
            detail={"ip_hash": ip_hash},
        )

    # Render HTML page
    updates_html_parts = []
    if not updates:
        updates_html_parts.append(
            '<div class="no-updates">No published updates have been posted for this matter yet.</div>'
        )
    else:
        for u in updates:
            u_text = html.escape(u.get("text", "")).replace("\n", "<br>")
            pub_at_str = u.get("published_at", "")[:10]
            updates_html_parts.append(
                f"""
                <article class="update-item">
                  <div class="update-meta">Published on {html.escape(pub_at_str)}</div>
                  <div class="update-body">{u_text}</div>
                </article>
                """
            )

    updates_html = "\n".join(updates_html_parts)

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(matter_title)} — {html.escape(firm_name)}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #f8fafc;
      color: #1e293b;
      margin: 0;
      padding: 32px 16px;
    }}
    .container {{
      max-width: 680px;
      margin: 0 auto;
    }}
    .header {{
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e2e8f0;
    }}
    .firm-name {{
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      margin-bottom: 6px;
    }}
    .matter-title {{
      font-size: 22px;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
      line-height: 1.3;
    }}
    .update-item {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .update-meta {{
      font-size: 12px;
      font-weight: 600;
      color: #0369a1;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .update-body {{
      font-size: 15px;
      line-height: 1.6;
      color: #334155;
    }}
    .no-updates {{
      background: #ffffff;
      border: 1px dashed #cbd5e1;
      border-radius: 8px;
      padding: 32px;
      text-align: center;
      color: #64748b;
      font-size: 14px;
    }}
    .footer {{
      margin-top: 40px;
      text-align: center;
      font-size: 12px;
      color: #94a3b8;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div class="firm-name">{html.escape(firm_name)}</div>
      <h1 class="matter-title">{html.escape(matter_title)}</h1>
    </header>
    <main>
      {updates_html}
    </main>
    <footer class="footer">
      Private and confidential client status report.
    </footer>
  </div>
</body>
</html>"""

    response = HttpResponse(page_html, content_type="text/html; charset=utf-8")
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "no-referrer"
    response["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'none';"
    )
    return response
