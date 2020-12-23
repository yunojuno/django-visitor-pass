from __future__ import annotations

from typing import Dict, Optional

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject


def visitor(request: HttpRequest) -> Dict[str, SimpleLazyObject]:
    """Add visitor context to template context (if found on the request)."""

    def _get_val() -> Optional[dict]:
        if request.visitor:
            return request.visitor.serialize()
        return None

    return {"visitor": SimpleLazyObject(_get_val)}
