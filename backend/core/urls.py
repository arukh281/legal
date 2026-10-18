"""URL configuration for lawyer_brain core."""

from django.contrib import admin
from django.urls import path

from core.api import api
from surface.views_public import public_share_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("share/<str:token>", public_share_view, name="public_share"),
]
