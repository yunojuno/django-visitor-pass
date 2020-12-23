from os import getenv

from django.conf import settings


def _setting(key: str, default: str) -> str:
    return getattr(settings, key, default) or getenv(key)


# session key used to store visitor.uuid
VISITOR_SESSION_KEY: str = _setting("VISITOR_SESSION_KEY", "visitor:session")

# key used to store visitor uuid on querystring
VISITOR_QUERYSTRING_KEY: str = _setting("VISITOR_QUERYSTRING_KEY", "vid")
