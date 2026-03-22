"""
Root conftest.py for pytest-django.

Overrides settings that are incompatible with the Django test client
(which uses 'testserver' as the HTTP host by default).
"""

import pytest


@pytest.fixture(autouse=True)
def allow_test_server_host(settings):
    """Add 'testserver' to ALLOWED_HOSTS so APIClient requests are not blocked."""
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
