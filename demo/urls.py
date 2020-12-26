from django.urls import path

from demo import views

app_name = "demo"

urlpatterns = [
    path("", views.index, name="index"),
    path("visitor", views.visitor_view, name="visitor_link"),
    path("create", views.create_visitor_link, name="create_visitor_link"),
    path("clear", views.clear_session_data, name="clear_session_data"),
]
