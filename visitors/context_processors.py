from __future__ import annotations

from django.http import HttpRequest


def visitor(request: HttpRequest) -> dict[str, object]:
    """Add visitor context to template context (if found on the request)."""
    if not request.visitor:
        return {"visitor": None}
    return {"visitor": request.visitor.serialize()}
