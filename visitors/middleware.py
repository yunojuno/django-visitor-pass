from __future__ import annotations

import logging
from typing import Callable

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from .models import Visitor, VisitorLog
from .settings import VISITOR_QUERYSTRING_KEY, VISITOR_SESSION_KEY

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
        except Visitor.DoesNotExist:
            return self.get_response(request)
        else:
            request.visitor = visitor
            request.user.is_visitor = True
            VisitorLog.objects.create_log(request)
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
            request.session[VISITOR_SESSION_KEY] = request.visitor.session_data
            return self.get_response(request)

        # We don't have a visitor object, but there may be one in the session
        if not (visitor_uuid := request.session.get(VISITOR_SESSION_KEY)):
            return self.get_response(request)

        try:
            visitor = Visitor.objects.get(uuid=visitor_uuid)
        except Visitor.DoesNotExist:
            del request.session[VISITOR_SESSION_KEY]
            return self.get_response(request)
        else:
            request.visitor = visitor
            request.user.is_visitor = True

        return self.get_response(request)


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
