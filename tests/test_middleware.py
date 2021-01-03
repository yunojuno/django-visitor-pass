import uuid
from typing import Optional
from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from visitors.middleware import VisitorRequestMiddleware, VisitorSessionMiddleware
from visitors.models import InvalidVisitorPass, Visitor
from visitors.settings import VISITOR_SESSION_KEY


class Session(dict):
    """Fake Session model used to support `session_key` property."""

    @property
    def session_key(self):
        return "foobar"

    def set_expiry(self, expiry: int) -> None:
        self.expiry = expiry


class TestVisitorMiddlewareBase:
    def request(self, url: str, user: Optional[User] = None):
        factory = RequestFactory()
        request = factory.get(url)
        request.user = user or AnonymousUser()
        request.session = Session()
        return request


class TestVisitorRequestMiddleware(TestVisitorMiddlewareBase):
    def test_no_token(self):
        request = self.request("/", AnonymousUser())
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    @pytest.mark.django_db
    def test_token_does_not_exist(self):
        request = self.request(f"/?vuid={uuid.uuid4()}")
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    @pytest.mark.django_db
    def test_token_is_invalid(self):
        visitor = Visitor.objects.create(email="fred@example.com", is_active=False)
        request = self.request(visitor.tokenise("/"))
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    @pytest.mark.django_db
    def test_valid_token(self):
        visitor = Visitor.objects.create(email="fred@example.com")
        request = self.request(visitor.tokenise("/"))
        middleware = VisitorRequestMiddleware(lambda r: r)
        middleware(request)
        assert request.user.is_visitor
        assert request.visitor == visitor


class TestVisitorSessionMiddleware(TestVisitorMiddlewareBase):
    def request(
        self,
        url: str,
        user: Optional[User] = None,
        is_visitor: bool = False,
        visitor: Visitor = None,
    ):
        request = super().request(url, user)
        request.user.is_visitor = is_visitor
        request.visitor = visitor
        return request

    @pytest.mark.django_db
    def test_visitor(self):
        """Check that request.visitor is stashed in session."""
        visitor = Visitor.objects.create(email="fred@example.com")
        request = self.request("/", is_visitor=True, visitor=visitor)
        assert not request.session.get(VISITOR_SESSION_KEY)
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert request.session[VISITOR_SESSION_KEY] == visitor.session_data

    @pytest.mark.django_db
    def test_no_visitor_no_session(self):
        """Check that no visitor on request or session passes."""
        request = self.request("/", is_visitor=False, visitor=None)
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor

    @pytest.mark.django_db
    def test_visitor_in_session(self):
        """Check no visitor on request, but in session."""
        request = self.request("/", is_visitor=False, visitor=None)
        visitor = Visitor.objects.create(email="fred@example.com")
        request.session[VISITOR_SESSION_KEY] = visitor.session_data
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert request.user.is_visitor
        assert request.visitor == visitor

    @pytest.mark.django_db
    def test_visitor_does_not_exist(self):
        """Check non-existant visitor in session."""
        request = self.request("/", is_visitor=False, visitor=None)
        request.session[VISITOR_SESSION_KEY] = str(uuid.uuid4())
        middleware = VisitorSessionMiddleware(lambda r: r)
        middleware(request)
        assert not request.user.is_visitor
        assert not request.visitor
        assert not request.session.get(VISITOR_SESSION_KEY)
