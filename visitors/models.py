from __future__ import annotations

import uuid
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.db import models
from django.db.models.deletion import CASCADE
from django.http.request import HttpRequest
from django.utils.timezone import now as tz_now
from django.utils.translation import gettext_lazy as _lazy

from .settings import VISITOR_QUERYSTRING_KEY


class Visitor(models.Model):
    """A temporary visitor (betwixt anonymous and authenticated)."""

    uuid = models.UUIDField(default=uuid.uuid4)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(db_index=True)
    scope = models.CharField(
        max_length=100, help_text=_lazy("Used to map request to view function")
    )
    created_at = models.DateTimeField(default=tz_now)
    context = models.JSONField(
        null=True,
        blank=True,
        help_text=_lazy("Used to store arbitrary contextual data."),
    )
    last_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.scope})"

    def __repr__(self) -> str:
        return f"<Visitor id={self.id} email='{self.email}' scope='{self.scope}'>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def session_data(self) -> str:
        return str(self.uuid)

    def serialize(self) -> dict:
        """
        Return JSON-serializable representation.

        Useful for template context and session data.

        """
        return {
            "uuid": str(self.uuid),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "scope": self.scope,
            "context": self.context,
        }

    def tokenise(self, url: str) -> str:
        """Combine url with querystring token."""
        # from https://stackoverflow.com/a/2506477/45698
        parts = list(urlparse(url))
        query = parse_qs(parts[4])
        query.update({VISITOR_QUERYSTRING_KEY: self.uuid})
        parts[4] = urlencode(query)
        return urlunparse(parts)


class VisitorLogManager(models.Manager):
    def create_log(self, request: HttpRequest) -> VisitorLog:
        """Extract values from HttpRequest and store locally."""
        return self.create(
            visitor=request.visitor,
            session_key=request.session.session_key or "",
            http_method=request.method,
            request_uri=request.path,
            query_string=request.META.get("QUERY_STRING", ""),
            http_user_agent=request.META.get("HTTP_USER_AGENT", ""),
            # we care about the domain more than the URL itself, so truncating
            # doesn't lose much useful information
            http_referer=request.META.get("HTTP_REFERER", ""),
            # X-Forwarded-For is used by convention when passing through
            # load balancers etc., as the REMOTE_ADDR is rewritten in transit
            remote_addr=(
                request.META.get("HTTP_X_FORWARDED_FOR")
                if "HTTP_X_FORWARDED_FOR" in request.META
                else request.META.get("REMOTE_ADDR")
            ),
        )


class VisitorLog(models.Model):
    """Log visitors."""

    visitor = models.ForeignKey(Visitor, related_name="visits", on_delete=CASCADE)
    session_key = models.CharField(blank=True, max_length=40)
    http_method = models.CharField(max_length=10)
    request_uri = models.URLField()
    remote_addr = models.CharField(max_length=100)
    query_string = models.TextField(blank=True)
    http_user_agent = models.TextField()
    http_referer = models.TextField()
    timestamp = models.DateTimeField(default=tz_now)

    objects = VisitorLogManager()
