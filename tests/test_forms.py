from __future__ import annotations

from uuid import uuid4

import pytest

from visitors.forms import SelfServiceForm


class TestSelfServiceForm:
    @pytest.mark.parametrize(
        "first_name,last_name,email,vuid,is_valid",
        [
            ("", "", "", None, False),
            ("John", "", "", None, False),
            ("John", "Doe", "", None, False),
            ("John", "Doe", "john@doe.com", None, False),
            ("John", "Doe", "john@doe.com", uuid4(), True),
            ("John", "Doe", "john.doe@example.com", uuid4(), False),
        ],
    )
    def test_form(self, first_name, last_name, email, vuid, is_valid):
        form = SelfServiceForm(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "vuid": vuid,
            }
        )
        assert form.is_valid() == is_valid
