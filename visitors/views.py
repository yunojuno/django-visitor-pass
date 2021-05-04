from __future__ import annotations

import uuid

from django import forms
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from .models import Visitor


class SelfServiceForm(forms.Form):
    """Form for capturing user info."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=True)
    vuid = forms.CharField(widget=forms.HiddenInput())
    redirect_to = forms.CharField(widget=forms.HiddenInput())


class SelfService(View):
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

    def get(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """Render the initial form."""
        visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
        redirect_to = request.GET.get("next")
        form = SelfServiceForm(
            initial={"vuid": visitor.uuid, "redirect_to": redirect_to}
        )
        return render(
            request,
            template_name="self_service.html",
            context={
                "visitor": visitor,
                "redirect_to": redirect_to,
                "form": form,
            },
        )

    def post(
        self,
        request: HttpRequest,
        visitor_uuid: uuid.UUID,
    ) -> HttpResponse:
        """Process the form and send the pass email."""
        visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
        form = SelfServiceForm(request.POST)
        if form.is_valid():
            visitor.first_name = form.cleaned_data["first_name"]
            visitor.last_name = form.cleaned_data["last_name"]
            visitor.email = form.cleaned_data["email"]
            visitor.is_active = True
            visitor.save()
            redirect_to = form.cleaned_data["redirect_to"]
            url = reverse("self-service-success", kwargs={"visitor_uuid": visitor_uuid})
            return HttpResponseRedirect(f"{url}?next={redirect_to}")
        return render(
            request,
            template_name="self_service.html",
            context={
                "visitor": visitor,
                "form": form,
            },
        )


def self_service_success(request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
    """Display the success page."""
    visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
    redirect_to = request.GET.get("next")
    return render(request, template_name="self_service_success.html", context={
        "visitor": visitor,
        "redirect_to": redirect_to
    })
