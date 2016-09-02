# -*- coding: utf-8 -*-
"""Test forms."""

from shop.public.forms import LoginForm
from shop.user.forms import RegisterForm, AddressForm


class TestRegisterForm:
    """Register form."""

    def test_validate_email_already_registered(self, user):
        """Enter email that is already registered."""
        form = RegisterForm(
            name='John Doe',
            email=user.email,
            password='example',
            confirm='example'
        )
        assert form.validate() is False
        assert 'Email already registered' in form.email.errors

    def test_validate_success(self, app):
        """Register with success."""
        form = RegisterForm(
            name='John Doe',
            email='new@test.test',
            password='example',
            confirm='example'
        )
        assert form.validate() is True


class TestLoginForm:
    """Login form."""

    def test_validate_success(self, user):
        """Login successful."""
        user.set_password('example')
        user.active = True
        user.save()
        form = LoginForm(email=user.email, password='example')
        assert form.validate() is True

    def test_validate_unknown_username(self, app):
        """Unknown username."""
        form = LoginForm(email='unknown', password='example')
        assert form.validate() is False
        assert 'Unknown email' in form.email.errors

    def test_validate_invalid_password(self, user):
        """Invalid password."""
        user.set_password('example')
        form = LoginForm(email=user.email, password='wrongpassword')
        assert form.validate() is False
        assert 'Invalid password' in form.password.errors

    def test_validate_inactive_user(self, user):
        """Inactive user."""
        user.active = False
        user.save()
        user.set_password('example')
        # Correct username and password, but user is not activated
        form = LoginForm(email=user.email, password='example')
        assert form.validate() is False
        assert 'User not activated' in form.email.errors


class TestAddressForm:

    def test_validate_success(self):
        form = AddressForm(
            name="Home Address",
            street="Street name",
            streetbis="StreetBis",
            zip="665788",
            city="City name",
            country=61,  # US
            subdivision=2494,  # Arizona
            phone=12345678
        )
        assert form.validate() is True

    def test_validate_invalid_subdivision(self):
        form = AddressForm(
            name="Home Address",
            street="Street name",
            streetbis="StreetBis",
            zip="665788",
            city="City name",
            country=61,  # US
            subdivision=3185,  # Bangalore
            phone=12345678
        )
        assert form.validate() is False
        assert 'Subdivision is not valid for the selected country.' \
               in form.subdivision.errors
