# -*- coding: utf-8 -*-
"""Model unit tests."""
import pytest
from shop.user.models import User

from .factories import UserFactory


@pytest.mark.usefixtures('app', 'delete_foo2')
class TestUser:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User({
            'name': 'foo',
            'email': 'foo2@bar.com'
        })
        user.save()
        retrieved = User.get_by_id(user.id)
        assert retrieved == user

    def test_password_is_nullable(self):
        """Test null password."""
        user = User(
            name='John Doe',
            email='foo2@bar.com'
        )
        user.save()
        assert user.password is None

    def test_factory(self):
        """Test user factory."""
        user = UserFactory(password='myprecious')
        assert bool(user.email)
        assert user.active is True

    def test_check_password(self):
        """Check password."""
        user = User(
            name='John Doe',
            email='foo2@bar.com',
            password='foobarbaz123'
        )
        user.save()
        assert user.check_password('foobarbaz123') is True
        assert user.check_password('barfoobaz') is False
