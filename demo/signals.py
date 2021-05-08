from django.dispatch import receiver

from visitors.models import Visitor
from visitors.signals import self_service_visitor_created


@receiver(self_service_visitor_created, sender=Visitor)
def send_visitor_notification(sender: object, visitor: Visitor) -> None:
    print(f"Sending visitor pass to: {visitor.email}")
