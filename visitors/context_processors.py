from __future__ import annotations

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject


def visitor(request: HttpRequest) -> dict[str, SimpleLazyObject]:
    """Add visitor context to template context (if found on the request)."""

    def _get_val() -> dict | None:
        if request.visitor:
            return request.visitor.serialize()
        return None

    return {"visitor": SimpleLazyObject(_get_val)}
