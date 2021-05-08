from django.apps import AppConfig


class DemoConfig(AppConfig):

    name = "demo"

    def ready(self) -> None:
        from demo.signals import send_visitor_notification
        return super().ready()
