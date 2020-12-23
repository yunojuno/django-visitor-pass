from __future__ import annotations

import json
from typing import Optional

from django.contrib import admin
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

    list_display = ("full_name", "scope", "created_at")
    readonly_fields = ("uuid", "created_at", "last_updated_at", "_context")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "scope",
        "created_at",
    )

    def _context(self, obj: Visitor) -> str:
        return pretty_print(obj.context)

    _context.short_description = "Context (prettified)"  # type: ignore


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ("visitor", "session_key", "remote_addr", "request_uri", "timestamp")
    readonly_fields = [f.name for f in VisitorLog._meta.fields]
    pass
