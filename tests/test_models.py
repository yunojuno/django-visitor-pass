import uuid

import pytest

from visitors.models import Visitor

TEST_UUID: str = "68201321-9dd2-4fb3-92b1-24367f38a7d6"


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
