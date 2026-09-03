import itertools

import pytest
from rest_framework.test import APIClient

from apps.users.models import User

_counter = itertools.count(1)


@pytest.fixture
def user_factory(db):
    def make(**overrides):
        i = next(_counter)
        data = {
            "nickname": f"pytest_user_{i}",
            "email": f"pytest-user-{i}@example.test",
            "password": "StrongTestPass_2026!",
            "first_name": "QA",
            "last_name": f"User{i}",
            "country": "DE",
            "nationality": "DE",
            "interface_language": "ru",
        }
        data.update(overrides)
        return User.objects.create_user(**data)
    return make


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user)
    return api_client, user
