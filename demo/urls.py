from django.contrib import admin
from django.urls import path

import demo.views

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("foo/", demo.views.foo, name="foo"),
    path("bar/", demo.views.bar, name="bar"),
    path("logout/", demo.views.logout, name="logout"),
    path("", demo.views.index, name="index"),
]
