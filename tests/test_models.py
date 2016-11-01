# -*- coding: utf-8 -*-
"""Model unit tests."""
import pytest
from shop.user.models import User
from shop.public.models import Country

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


@pytest.mark.usefixtures('app')
class TestCountry:
    def test_get_list(self):
        countries = Country.get_list()
        assert len(countries) > 0
        assert countries[0].code
        assert countries[0].name
        assert countries[0].subdivisions

    def test_from_code(self):
        us = Country.from_code('US')
        assert us.code == 'US'
        assert us == Country.from_code('Us')
        assert us == Country.from_code('us')

    def test_subdivisions(self):
        us = Country.from_code('US')
        codes = [state.code for state in us.subdivisions]
        assert 'CA' in codes
        assert 'FL' in codes

    def test_subdvision_from_code(self):
        us = Country.from_code('US')
        ca = us.get_subdivision('CA')
        assert ca
        assert ca.code == 'CA'
        assert ca.name == 'California'

        assert ca == us.get_subdivision('ca')

        nope = us.get_subdivision('XX')
        assert nope is None
