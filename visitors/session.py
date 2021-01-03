from django.http.request import HttpRequest

from visitors.settings import VISITOR_SESSION_EXPIRY, VISITOR_SESSION_KEY


def stash_visitor_uuid(request: HttpRequest) -> None:
    """Store request visitor data in session."""
    request.session[VISITOR_SESSION_KEY] = request.visitor.session_data
    if request.user.is_anonymous:
        request.session.set_expiry(VISITOR_SESSION_EXPIRY)


def get_visitor_uuid(request: HttpRequest) -> str:
    """Return visitor data from session."""
    return request.session.get(VISITOR_SESSION_KEY, "")


def clear_visitor_uuid(request: HttpRequest) -> None:
    """Remove visitor data from session."""
    request.session.pop(VISITOR_SESSION_KEY, "")
