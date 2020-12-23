from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseForbidden
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

# universal scope - essentially unscoped access
SCOPE_ANY = "*"


def _get_request_arg(*args: Any) -> Optional[HttpRequest]:
    """Extract the arg that is an HttpRequest object."""
    for arg in args:
        if isinstance(arg, HttpRequest):
            return arg
    return None


def allow_visitor(  # noqa: C901
    view_func: Optional[Callable] = None,
    scope: str = "*",
    bypass: Callable = lambda u: u.is_authenticated,
) -> Callable:
    """
    Decorate view functions that supports Visitor access.

    The 'scope' param is mapped to the request.visitor.scope attribute - if
    the scope is SCOPE_ANY then this is ignored.

    The 'bypass' param is a callable (lambda) that can be used to provide
    exceptions to the scope. The default is to allow authenticated users
    to bypass the restriction. To prevent this use `lambda u: False`.

    Errors are trapped and returned as HttpResponseForbidden responses, with
    the original error as the `response.error` property.

    For more details on decorators with optional args, see:
    https://blogs.it.ox.ac.uk/inapickle/2012/01/05/python-decorators-with-optional-arguments/

    """
    if not scope:
        raise ValueError("Decorator scope cannot be empty.")

    if view_func is None:
        return functools.partial(allow_visitor, scope=scope, bypass=bypass)

    @functools.wraps(view_func)
    def inner(*args: Any, **kwargs: Any) -> HttpResponse:
        # should never happen, but keeps mypy happy as it _could_
        if not view_func:
            raise ValueError("Callable (view_func) missing.")
        # HACK: if this is decorating a method, then the first arg will be
        # the object (self), and not the request. In order to make this work
        # with functions and methods we need to determine where the request
        # arg is.
        request = _get_request_arg(*args)
        if not request:
            raise ValueError("Request argument missing.")

        if bypass(request.user):
            return view_func(*args, **kwargs)

        if not request.user.is_visitor:
            return HttpResponseForbidden(_("Visitor access denied"))

        if scope == SCOPE_ANY:
            return view_func(*args, **kwargs)

        if request.visitor.scope == scope:
            return view_func(*args, **kwargs)

        return HttpResponseForbidden(_("Invalid visitor scope"))

    return inner
