from django.urls import path

from . import views

app_name = "visitors"

urlpatterns = [
    path(
        "self-service/<uuid:visitor_uuid>/",
        views.SelfServiceRequest.as_view(),
        name="self-service",
    ),
    path(
        "self-service/<uuid:visitor_uuid>/success/",
        views.SelfServiceSuccess.as_view(),
        name="self-service-success",
    ),
]
