from __future__ import annotations

from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now as tz_now

from visitors.exceptions import InvalidVisitorPass
from visitors.models import Visitor
from visitors.views import SelfServiceRequest


@pytest.mark.django_db
class TestSelfService:
    @mock.patch("visitors.views.render")
    @pytest.mark.parametrize(
        "is_active,has_expired,error",
        [
            (True, True, InvalidVisitorPass),
            (True, False, InvalidVisitorPass),
            (False, True, InvalidVisitorPass),
            (False, False, None),
        ],
    )
    def test_get(
        self,
        mock_render,
        rf: RequestFactory,
        visitor: Visitor,
        is_active: bool,
        has_expired: bool,
        error: Exception,
    ) -> None:
        request = rf.get("/")
        request.visitor = visitor
        visitor.is_active = is_active
        if has_expired:
            visitor.expires_at = tz_now() - timedelta(seconds=1)
        visitor.save()
        view = SelfServiceRequest()
        assert visitor.has_expired == has_expired
        assert visitor.is_active == is_active
        if error:
            with pytest.raises(error):
                view.dispatch(request, visitor.uuid)
        else:
            resp = view.dispatch(request, visitor.uuid)
            assert resp.status_code == mock_render.return_value.status_code
            mock_render.assert_called_once_with(
                request,
                template_name="visitors/self_service_request.html",
                context={"visitor": visitor, "form": mock.ANY},
            )

    @mock.patch.object(SelfServiceRequest, "get_template_name")
    @mock.patch("visitors.views.render")
    def test_template_override(
        self,
        mock_render,
        mock_template_name,
        rf: RequestFactory,
        visitor: Visitor,
    ) -> None:
        request = rf.get("/")
        request.visitor = visitor
        visitor.is_active = False
        visitor.save()
        view = SelfServiceRequest(visitor=visitor)
        _ = view.dispatch(request, visitor.uuid)
        mock_template_name.assert_called_once_with()
        mock_render.assert_called_once_with(
            request,
            template_name=mock_template_name.return_value,
            context={"visitor": visitor, "form": mock.ANY},
        )

    def test_post_404(self, rf: RequestFactory) -> None:
        request = rf.post("/")
        view = SelfServiceRequest()
        with pytest.raises(Http404):
            view.dispatch(request, visitor_uuid=uuid4())

    def test_post_valid(self, rf: RequestFactory, temp_visitor: Visitor) -> None:
        assert not temp_visitor.is_active
        request = rf.post(
            "/",
            {
                "vuid": temp_visitor.uuid,
                "first_name": "Henry",
                "last_name": "Root",
                "email": "henry@altavista.com",
            },
        )
        request.visitor = temp_visitor
        view = SelfServiceRequest()
        resp = view.dispatch(request, visitor_uuid=temp_visitor.uuid)
        assert resp.status_code == 302
        temp_visitor.refresh_from_db()
        assert temp_visitor.is_active
        assert temp_visitor.first_name == "Henry"
        assert temp_visitor.last_name == "Root"
        assert temp_visitor.email == "henry@altavista.com"
        assert resp.url == reverse(
            "visitors:self-service-success",
            kwargs={"visitor_uuid": temp_visitor.uuid},
        )

    def test_post_invalid(self, rf: RequestFactory, temp_visitor: Visitor) -> None:
        assert not temp_visitor.is_active
        request = rf.post(
            "/",
            {
                "vuid": temp_visitor.uuid,
                "first_name": "Henry",
                "last_name": "Root",
                "email": "henry",
            },
        )
        request.visitor = temp_visitor
        view = SelfServiceRequest()
        resp = view.dispatch(request, visitor_uuid=temp_visitor.uuid)
        assert resp.status_code == 200
