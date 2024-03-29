from django.contrib import admin
from django.urls import include, path

import demo.views
from visitors import urls as visitor_urls

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("foo/", demo.views.foo, name="foo"),
    path("bar/", demo.views.bar, name="bar"),
    path("logout/", demo.views.logout, name="logout"),
    path("visitors/", include(visitor_urls, namespace="visitors")),
    path("", demo.views.index, name="index"),
]
