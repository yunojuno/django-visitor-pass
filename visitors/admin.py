from __future__ import annotations

import json
from typing import Optional

from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.safestring import mark_safe

from .models import Visitor, VisitorLog


def pretty_print(data: Optional[dict]) -> str:
    """Convert dict into formatted HTML."""
    if data is None:
        return ""
    pretty = json.dumps(data, sort_keys=True, indent=4, separators=(",", ": "))
    html = pretty.replace(" ", "&nbsp;").replace("\n", "<br>")
    return mark_safe("<pre><code>%s</code></pre>" % html)


@admin.register(Visitor)
class VisitorsAdmin(admin.ModelAdmin):
    """Admin model for Visitor objects."""

    def deactivate(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Call deactivate on all selected Visitor objects."""
        count = queryset.count()
        for obj in queryset:
            obj.deactivate()
        self.message_user(
            request, f"{count} passes have been disabled.", messages.SUCCESS
        )

    deactivate.short_description = "Deactivate selected Visitor passes"  # type: ignore

    def reactivate(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Reactivate all selected Visitor objects."""
        count = queryset.count()
        for obj in queryset:
            obj.reactivate()
        self.message_user(
            request, f"{count} passes have been activated.", messages.SUCCESS
        )

    reactivate.short_description = "Reactivate selected Visitor passes"  # type: ignore

    actions = (deactivate, reactivate)
    list_filter = ("scope",)
    list_display = (
        "scope",
        "email",
        "created_at",
        "expires_at",
        "is_active",
        "_is_valid",
    )
    readonly_fields = (
        "uuid",
        "created_at",
        "last_updated_at",
        "_context",
        "is_active",
        "expires_at",
    )
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "scope",
        "created_at",
    )

    def _is_valid(self, obj: Visitor) -> bool:
        return obj.is_valid

    _is_valid.boolean = True  # type: ignore

    def _context(self, obj: Visitor) -> str:
        return pretty_print(obj.context)

    _context.short_description = "Context (prettified)"  # type: ignore


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = (
        "visitor",
        "session_key",
        "remote_addr",
        "request_uri",
        "status_code",
        "timestamp",
    )
    readonly_fields = [f.name for f in VisitorLog._meta.fields]
    pass
