from django.apps import AppConfig


class DemoConfig(AppConfig):

    name = "demo"

    def ready(self) -> None:
        from demo import signals  # noqa: F401

        return super().ready()
