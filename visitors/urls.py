from django.urls import path

from . import views

app_name = "visitors"

urlpatterns = [
    path(
        "self-service/<uuid:visitor_uuid>/",
        views.SelfService.as_view(),
        name="self-service",
    ),
]
