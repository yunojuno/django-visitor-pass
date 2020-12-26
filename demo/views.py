from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from visitors import session
from visitors.decorators import check_visitor_scope
from visitors.models import Visitor


def index(request: HttpRequest) -> HttpResponse:
    """Homepage view."""
    return render(request, "index.html")


@check_visitor_scope(scope="abracadabra", bypass_func=lambda u: False)
def visitor_view(request: HttpRequest) -> HttpResponse:
    """Homepage view."""
    return render(request, "index.html")


def create_visitor_link(request: HttpRequest) -> HttpResponse:
    """Create a new visitor link."""
    visitor = Visitor.objects.create(email="test@example.com", scope="abracadabra")
    return render(request, "index.html", {"visitor_uuid": visitor.uuid})


def clear_session_data(request: HttpRequest) -> HttpResponse:
    """Clear visitor data from session."""
    session.clear_visitor_uuid(request)
    return redirect(reverse("demo:index"))
    # return render(request, "index.html")
