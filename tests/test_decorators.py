from __future__ import annotations

from typing import Optional

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from visitors.decorators import check_visitor_scope
from visitors.models import Visitor


@pytest.mark.django_db
class TestDecorators:
    def _request(
        self, user: Optional[User] = None, visitor: Optional[Visitor] = None
    ) -> HttpRequest:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user or AnonymousUser()
        request.visitor = visitor
        request.user.is_visitor = visitor is not None
        return request

    def test_no_access(self):
        request = self._request()

        @check_visitor_scope(scope="foo")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            response = view(request)

    def test_incorrect_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self._request(visitor=visitor)

        @check_visitor_scope(scope="bar")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            response = view(request)

    def test_correct_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self._request(visitor=visitor)

        @check_visitor_scope(scope="foo")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_any_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self._request(visitor=visitor)

        @check_visitor_scope(scope="*")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__True(self):
        """Check that the bypass param works."""
        user = User(username="fred")
        request = self._request(user=user)

        @check_visitor_scope(scope="foo", bypass_func=lambda r: True)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__False(self):
        user = User(username="fred")
        request = self._request(user=user)

        @check_visitor_scope(scope="foo", bypass_func=lambda r: False)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            response = view(request)
