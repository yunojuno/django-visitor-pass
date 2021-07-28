from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from visitors.decorators import user_is_visitor
from visitors.models import Visitor, VisitorLog


@pytest.mark.django_db
class TestDecorators:
    def _request(
        self, user: User | None = None, visitor: Visitor | None = None
    ) -> HttpRequest:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user or AnonymousUser()
        request.visitor = visitor
        request.user.is_visitor = visitor is not None
        request.session = SessionBase()
        return request

    def test_no_access(self) -> None:
        request = self._request()

        @user_is_visitor(scope="foo")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            _ = view(request)

    def test_incorrect_scope(self, visitor: Visitor) -> None:
        request = self._request(visitor=visitor)

        @user_is_visitor(scope="bar")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            _ = view(request)

    def test_correct_scope(self, visitor: Visitor) -> None:
        request = self._request(visitor=visitor)

        @user_is_visitor(scope="foo")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_any_scope(self, visitor: Visitor) -> None:
        request = self._request(visitor=visitor)

        @user_is_visitor(scope="*")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__True(self, user: User) -> None:
        """Check that the bypass param works."""
        request = self._request(user=user)

        @user_is_visitor(scope="foo", bypass_func=lambda r: True)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__False(self, user: User) -> None:
        request = self._request(user=user)

        @user_is_visitor(scope="foo", bypass_func=lambda r: False)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied):
            _ = view(request)

    def test_logging(self, visitor: Visitor) -> None:
        request = self._request(visitor=visitor)

        @user_is_visitor(scope="foo")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        log: VisitorLog = VisitorLog.objects.get()
        assert response.status_code == 200
        assert log.status_code == 200

    def test_logging__False(self, visitor: Visitor) -> None:
        request = self._request(visitor=visitor)

        @user_is_visitor(scope="foo", log_visit=False)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        _ = view(request)
        assert VisitorLog.objects.count() == 0

    def test_self_service_redirect(self):
        request = self._request(visitor=None)

        @user_is_visitor(scope="foo", self_service=True)
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 302
        visitor = Visitor.objects.get()
        assert visitor.is_self_service
        assert not visitor.is_active
        assert response.url == reverse(
            "visitors:self-service", kwargs={"visitor_uuid": visitor.uuid}
        )
