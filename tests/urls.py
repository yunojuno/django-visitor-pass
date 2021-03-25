from django.contrib import admin
from django.urls import path
from django.urls.conf import include

from visitors import urls as visitor_urls

from . import views

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("visitors/", include(visitor_urls, namespace="visitors")),
    path("foo/", views.foo),
    path("bar/", views.bar),
]
