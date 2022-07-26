import pytest
from django.contrib.auth.models import User

from visitors.models import Visitor


@pytest.fixture
def visitor() -> Visitor:
    return Visitor.objects.create(email="fred@example.com", scope="foo")


@pytest.fixture
def temp_visitor() -> Visitor:
    return Visitor.objects.create_temp_visitor(
        scope="foo",
        redirect_to="/foo",
    )


@pytest.fixture
def user() -> User:
    return User.objects.create(username="Fred")
