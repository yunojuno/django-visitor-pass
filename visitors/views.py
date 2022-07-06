from __future__ import annotations

import uuid
from typing import Any

from django import forms
from django.http import Http404, HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from visitors.exceptions import InvalidVisitorPass

from .forms import SelfServiceForm
from .models import Visitor
from .signals import self_service_visitor_created


class SelfServiceBase(View):
    """Base view for self-service pages."""

    # default visitor request templates
    template_name = ""

    def __init__(self, **kwargs: Any) -> None:
        self.visitor: Visitor | None = None
        super().__init__(**kwargs)

    def get_template_name(self) -> str:
        """Return the path to the template to render."""
        if self.template_name:
            return self.template_name
        raise NotImplementedError("Missing template_name property.")

    def get_context_data(self, **form_kwargs: object) -> dict:
        """
        Return the context passed to the template.

        Default passes the Visitor object and anything that is passed in
        as form_kwargs. This is essentially a noop that exists only so
        that it can be overridden.

        """
        context: dict = {"visitor": self.visitor}
        context.update(form_kwargs)
        return context

    def dispatch(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """Override default view dispatch to set visitor attr."""
        self.visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
        return super().dispatch(request, visitor_uuid)


class SelfServiceRequest(SelfServiceBase):
    """
    Enable users to create their own visitor passes.

    If a visitor pass is marked as `auto-enroll` then a user can
    create their own pass. In this model, an user without access
    would be redirected to this view, where they can input their
    own name and email. They receive their own visitor pass.

    The purpose of this is to add some protection to 'obscure'
    urls. e.g. those that rely on an unguessable uuid - instead
    of making those URLs completely public, we can force the user
    to give us their name / email (name can be faked, but they
    will require access to the email).

    """

    # default visitor request templates
    template_name = "visitors/self_service_request.html"
    form_class = SelfServiceForm

    def get_form_class(self) -> forms.Form:
        """Return the SelfServiceForm used by the template."""
        return self.form_class

    def get_form_initial(self) -> dict:
        """Return the initial data used for the form."""
        if not self.visitor:  # should never occur - set in dispatch()
            raise Http404
        return {"vuid": self.visitor.uuid}

    def get_redirect_url(self) -> str:
        """Return the post-POST success url."""
        if not self.visitor:  # should never occur - set in dispatch()
            raise Http404
        return reverse(
            "visitors:self-service-success",
            kwargs={"visitor_uuid": self.visitor.uuid},
        )

    def validate_visitor(self) -> Visitor:
        """Validate the local Visitor object."""
        if not self.visitor:  # should never occur - set in dispatch()
            raise Http404
        if self.visitor.is_active:
            raise InvalidVisitorPass("Visitor pass has already been activated")
        if self.visitor.has_expired:
            raise InvalidVisitorPass("Visitor pass has expired")
        return self.visitor

    def get(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """Render the initial form."""
        _ = self.validate_visitor()
        template = self.get_template_name()
        form = self.get_form_class()(initial=self.get_form_initial())
        context = self.get_context_data(form=form)
        return render(request, template_name=template, context=context)

    def post(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """
        Process the form and send the pass email.

        The core function here is to update the visitor object with the
        details from the form. Once that is done the visitor pass is
        active and can be sent to the user. This view fires the
        `self_service_visitor_created` signal - you should use this to
        send out the notification.

        """
        visitor = self.validate_visitor()
        form = self.get_form_class()(request.POST)
        if form.is_valid():
            visitor.first_name = form.cleaned_data["first_name"]
            visitor.last_name = form.cleaned_data["last_name"]
            visitor.email = form.cleaned_data["email"]
            visitor.reactivate()
            # hook into this to send the email notification to the user.
            self_service_visitor_created.send(sender=self.__class__, visitor=visitor)
            return HttpResponseRedirect(self.get_redirect_url())
        template = self.get_template_name()
        context = self.get_context_data(form=form)
        return render(request, template_name=template, context=context)


class SelfServiceSuccess(SelfServiceBase):
    """Render the page that appears after a successful self-service request."""

    template_name = "visitors/self_service_success.html"

    def get(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        return render(
            request,
            template_name=self.get_template_name(),
            context=self.get_context_data(),
        )
