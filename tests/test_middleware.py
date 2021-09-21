import uuid
from typing import Optional

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.http.request import HttpRequest
from django.test import RequestFactory

from visitors.middleware import VisitorRequestMiddleware, VisitorSessionMiddleware
from visitors.models import Visitor
from visitors.settings import VISITOR_SESSION_KEY


@pytest.fixture
def visitor() -> Visitor:
    return Visitor.objects.create(email="fred@example.com", scope="foo")


class Session(dict):
    """Fake Session model used to support `session_key` property."""

    @property
    def session_key(self) -> str:
        return "foobar"

    def set_expiry(self, expiry: int) -> None:
        self.expiry = expiry


class TestVisitorMiddlewareBase:
    def request(self, url: str, user: Optional[User] = None) -> HttpRequest:
        factory = RequestFactory()
        request = factory.get(url)
        request.user = user or AnonymousUser()
        request.session = Session()
        return request


@pytest.mark.django_db
class TestVisitorRequestMiddleware(TestVisitorMiddlewareBase):
    def test_no_token(self) -> None:
        request = self.request("/", AnonymousUser())
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    def test_token_does_not_exist(self) -> None:
        request = self.request(f"/?vuid={uuid.uuid4()}")
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    def test_token_is_invalid(self, visitor: Visitor) -> None:
        visitor.deactivate()
        request = self.request(visitor.tokenise("/"))
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    def test_token_validation_error(self, visitor: Visitor) -> None:
        request = self.request("/?vuid=123")
        middleware = VisitorRequestMiddleware(lambda r: r)
        resp = middleware(request)
        assert resp.status_code == 400
        assert not request.user.is_visitor
        assert not request.visitor

    def test_valid_token(self, visitor: Visitor) -> None:
        request = self.request(visitor.tokenise("/"))
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert request.user.is_visitor
        assert request.visitor == visitor


@pytest.mark.django_db
class TestVisitorSessionMiddleware(TestVisitorMiddlewareBase):
    def request(
        self,
        url: str,
        user: Optional[User] = None,
        is_visitor: bool = False,
        visitor: Visitor = None,
    ) -> HttpRequest:
        request = super().request(url, user)
        request.user.is_visitor = is_visitor
        request.visitor = visitor
        return request

    def test_visitor(self, visitor: Visitor) -> None:
        """Check that request.visitor is stashed in session."""
        request = self.request("/", is_visitor=True, visitor=visitor)
        assert not request.session.get(VISITOR_SESSION_KEY)
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert request.session[VISITOR_SESSION_KEY] == visitor.session_data

    def test_no_visitor_no_session(self) -> None:
        """Check that no visitor on request or session passes."""
        request = self.request("/", is_visitor=False, visitor=None)
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    def test_visitor_in_session(self, visitor: Visitor) -> None:
        """Check no visitor on request, but in session."""
        request = self.request("/", is_visitor=False, visitor=None)
        request.session[VISITOR_SESSION_KEY] = visitor.session_data
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert request.user.is_visitor
        assert request.visitor == visitor

    def test_visitor_does_not_exist(self) -> None:
        """Check non-existant visitor in session."""
        request = self.request("/", is_visitor=False, visitor=None)
        request.session[VISITOR_SESSION_KEY] = str(uuid.uuid4())
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor
        assert not request.session.get(VISITOR_SESSION_KEY)
