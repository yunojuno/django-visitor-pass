from django.contrib import admin
from django.urls import path

from . import views

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("foo/", views.foo),
]
