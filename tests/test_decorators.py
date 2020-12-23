from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase

from visitors.decorators import allow_visitor
from visitors.models import Visitor


class DecoratorTests(TestCase):
    """allow_visitor decorator tests."""

    def request(
        self, user: Optional[User] = None, visitor: Optional[Visitor] = None
    ) -> HttpRequest:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user or AnonymousUser()
        request.visitor = visitor
        request.user.is_visitor = visitor is not None
        return request

    def test_no_access(self):
        request = self.request()
        assert not request.user.is_visitor
        assert not request.visitor

        @allow_visitor(scope="foo")
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 403
        assert response.content == "Visitor access denied".encode(response.charset)

    def test_incorrect_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self.request(visitor=visitor)
        assert request.user.is_visitor
        assert request.visitor == visitor

        @allow_visitor(scope="bar")
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 403
        assert response.content == "Invalid visitor scope".encode(response.charset)

    def test_correct_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self.request(visitor=visitor)
        assert request.user.is_visitor
        assert request.visitor == visitor

        @allow_visitor(scope="foo")
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_any_scope(self):
        visitor = Visitor.objects.create(email="fred@example.com", scope="foo")
        request = self.request(visitor=visitor)
        assert request.user.is_visitor
        assert request.visitor == visitor

        @allow_visitor(scope="*")
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__True(self):
        """Check that the bypass param works."""
        user = User(first_name="fred")
        request = self.request(user=user)
        assert not request.user.is_visitor
        assert not request.visitor

        @allow_visitor(scope="foo", bypass=lambda u: True)
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_bypass__False(self):
        user = User(first_name="fred")
        request = self.request(user=user)
        assert not request.user.is_visitor
        assert not request.visitor

        @allow_visitor(scope="foo", bypass=lambda u: False)
        def view(request):
            return HttpResponse("OK")

        response = view(request)
        assert response.status_code == 403
        assert response.content == b"Visitor access denied"
