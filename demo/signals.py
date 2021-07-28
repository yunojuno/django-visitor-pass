import logging
from typing import cast

from django.dispatch import receiver

from visitors.models import Visitor
from visitors.signals import self_service_visitor_created

logger = logging.getLogger(__name__)


@receiver(self_service_visitor_created)
def send_visitor_notification(sender: object, **kwargs: object) -> None:
    visitor = cast(Visitor, kwargs["visitor"])
    logger.info(f"Sending visitor pass to: {visitor.email}")
