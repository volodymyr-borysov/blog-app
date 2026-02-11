"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides fixtures
available to all test files.
"""

import pytest


def get_user_model():
    """Lazy-load User model to avoid Django configuration issues at import time."""
    from django.contrib.auth import get_user_model as _get_user_model

    return _get_user_model()


@pytest.fixture
def client():
    """Return a Django test client."""
    from django.test import Client

    return Client()


@pytest.fixture
def api_client():
    """Return a DRF API client (if using DRF)."""
    from django.test import Client

    return Client()


@pytest.fixture
def create_user():
    """Factory fixture to create users."""

    def _create_user(
        email="test@example.com", username="testuser", password="TestPass123!", **kwargs
    ):
        User = get_user_model()
        return User.objects.create_user(email=email, username=username, password=password, **kwargs)

    return _create_user


@pytest.fixture
def user(create_user):
    """Create and return a regular user."""
    return create_user()


@pytest.fixture
def authenticated_user(create_user):
    """Create and return an authenticated user."""
    return create_user()


@pytest.fixture
def staff_user(create_user):
    """Create and return a staff user."""
    user = create_user(email="staff@example.com", username="staffuser", is_staff=True)
    return user


@pytest.fixture
def superuser():
    """Create and return a superuser."""
    User = get_user_model()
    return User.objects.create_superuser(
        email="admin@example.com", username="admin", password="AdminPass123!"
    )
