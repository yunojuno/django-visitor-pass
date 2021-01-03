import datetime
import uuid

import pytest
from django.utils.timezone import now as tz_now

from visitors.models import InvalidVisitorPass, Visitor

TEST_UUID: str = "68201321-9dd2-4fb3-92b1-24367f38a7d6"

TODAY: datetime.datetime = tz_now()
ONE_DAY: datetime.timedelta = datetime.timedelta(days=1)
TOMORROW: datetime.datetime = TODAY + ONE_DAY
YESTERDAY: datetime.datetime = TODAY - ONE_DAY


@pytest.mark.parametrize(
    "url_in,url_out",
    (
        ("google.com", f"google.com?vuid={TEST_UUID}"),
        ("google.com?vuid=123", f"google.com?vuid={TEST_UUID}"),
    ),
)
def test_visitor_tokenise(url_in, url_out):
    visitor = Visitor(uuid=uuid.UUID(TEST_UUID))
    assert visitor.tokenise(url_in) == url_out


@pytest.mark.django_db
def test_deactivate():
    visitor = Visitor.objects.create(email="foo@bar.com")
    assert visitor.is_active
    visitor.deactivate()
    assert not visitor.is_active
    visitor.refresh_from_db()
    assert not visitor.is_active


@pytest.mark.django_db
def test_reactivate():
    visitor = Visitor.objects.create(
        email="foo@bar.com", is_active=False, expires_at=YESTERDAY
    )
    assert not visitor.is_active
    assert visitor.has_expired
    assert not visitor.is_valid
    visitor.reactivate()
    assert visitor.is_active
    assert not visitor.has_expired
    assert visitor.is_valid
    visitor.refresh_from_db()
    assert visitor.is_active
    assert not visitor.has_expired
    assert visitor.is_valid


@pytest.mark.parametrize(
    "is_active,expires_at,is_valid",
    (
        (True, TOMORROW, True),
        (False, TOMORROW, False),
        (False, YESTERDAY, False),
        (True, YESTERDAY, False),
    ),
)
def test_validate(is_active, expires_at, is_valid):
    visitor = Visitor(is_active=is_active, expires_at=expires_at)
    assert visitor.is_active == is_active
    assert visitor.has_expired == bool(expires_at < TODAY)
    if is_valid:
        visitor.validate()
        return
    with pytest.raises(InvalidVisitorPass):
        visitor.validate()


@pytest.mark.parametrize(
    "is_active,expires_at,is_valid",
    (
        (True, TOMORROW, True),
        (False, TOMORROW, False),
        (False, YESTERDAY, False),
        (True, YESTERDAY, False),
        (True, None, True),
        (False, None, False),
    ),
)
def test_is_valid(is_active, expires_at, is_valid):
    visitor = Visitor(is_active=is_active, expires_at=expires_at)
    assert visitor.is_valid == is_valid


def test_defaults():
    visitor = Visitor()
    assert visitor.created_at
    assert visitor.expires_at == visitor.created_at + Visitor.DEFAULT_TOKEN_EXPIRY


@pytest.mark.parametrize(
    "expires_at,has_expired",
    (
        (TOMORROW, False),
        (YESTERDAY, True),
        (None, False),
    ),
)
def test_has_expired(expires_at, has_expired):
    visitor = Visitor()
    visitor.expires_at = expires_at
    assert visitor.has_expired == has_expired
