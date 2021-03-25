from django.core.exceptions import PermissionDenied


class InvalidVisitorPass(Exception):
    pass


class VisitorAccessDenied(PermissionDenied):
    """Error raised by decorator when visitor is invalid."""

    def __init__(self, msg: str, scope: str, self_service: bool) -> None:
        super().__init__(msg)
        self.scope = scope
        self.self_service = self_service
