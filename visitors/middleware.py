from __future__ import annotations

import logging
from typing import Callable, Optional

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from . import session
from .exceptions import VisitorAccessDenied
from .models import InvalidVisitorPass, Visitor
from .settings import VISITOR_QUERYSTRING_KEY

logger = logging.getLogger(__name__)


class VisitorRequestMiddleware:
    """Extract visitor token from incoming request."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.visitor = None
        request.user.is_visitor = False
        visitor_uuid = request.GET.get(VISITOR_QUERYSTRING_KEY)
        if not visitor_uuid:
            return self.get_response(request)
        try:
            visitor = Visitor.objects.get(uuid=visitor_uuid)
            visitor.validate()
        except Visitor.DoesNotExist:
            logger.debug("Visitor pass does not exist: %s", visitor_uuid)
            return self.get_response(request)
        except InvalidVisitorPass as ex:
            logger.debug("Invalid access request: %s", ex)
            return self.get_response(request)
        else:
            request.visitor = visitor
            request.user.is_visitor = True
        return self.get_response(request)


class VisitorSessionMiddleware:
    """Extract visitor info from session and update request user."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Update request.user if any visitor vars are found in session.

        This middleware should run after the VisitorRequestMiddleware. If
        a request comes in without a visitor token in the querystring, we
        need to check the request.session to see if any visitor data was
        stashed previously.

        The first time this middleware runs after a new session is created
        this will push the `request.visitor` info into the session.
        Subsequent requests will then get the data out of the session.

        """
        # This will only be true directly after VisitorRequestMiddleware
        # has set the values. All subsequent requests in the session will
        # start with is_visitor=False and pick up the visitor info from
        # the session.
        if request.visitor:
            session.stash_visitor_uuid(request)
            return self.get_response(request)

        # We don't have a visitor object, but there may be one in the session
        if not (visitor_uuid := session.get_visitor_uuid(request)):
            return self.get_response(request)

        try:
            visitor = Visitor.objects.get(
                uuid=visitor_uuid,
                is_active=True,
            )
        except Visitor.DoesNotExist:
            session.clear_visitor_uuid(request)
            return self.get_response(request)
        else:
            request.visitor = visitor
            request.user.is_visitor = True

        return self.get_response(request)


class VisitorSelfServiceMiddleware:
    """Handle auto-enrollment."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> Optional[HttpResponse]:
        """
        Handle VisitorAccessDenied errors.

        If we have an AnonymousUser and `self_service=True` then we
        send the user to the autoenroll page.

        """
        if request.user.is_authenticated:
            return None
        if not isinstance(exception, VisitorAccessDenied):
            return None
        if not exception.self_service:
            return None

        # create an inactive token for the time being. This will be used by
        # the auto-enroll view. The user fills in their name and email, which
        # overwrites the blank values here, and sets the token to be active.
        visitor = Visitor.objects.create(
            email="anon@example.com",
            scope=exception.scope,
            is_active=False,
            context={"self-service": True},
        )
        return HttpResponseRedirect(
            reverse("visitors:self-service", kwargs={"visitor_uuid": visitor.uuid})
        )


class VisitorDebugMiddleware:
    """Print out visitor info - DEBUG only."""

    def __init__(self, get_response: Callable):
        if not settings.DEBUG:
            raise MiddlewareNotUsed("VisitorDebugMiddleware disabled")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        logger.debug("request.user.is_visitor: %s", request.user.is_visitor)
        if request.user.is_visitor:
            logger.debug("request.visitor: %s", request.visitor)
        return self.get_response(request)
