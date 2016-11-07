# -*- coding: utf-8 -*-
"""Test forms."""

from shop.public.forms import LoginForm
from shop.user.forms import RegisterForm, AddressForm
from shop.user.models import Address


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
        form = LoginForm(email='unknown@hello.com', password='example')
        assert form.validate() is False
        assert 'Invalid login credentials' in form.email.errors

    def test_validate_invalid_password(self, user):
        """Invalid password."""
        user.set_password('example')
        form = LoginForm(email=user.email, password='wrongpassword')
        assert form.validate() is False
        assert form.errors
        assert 'Invalid login credentials' in form.email.errors

    def test_validate_inactive_user(self, user):
        """Inactive user."""
        user.active = False
        user.save()
        user.set_password('example')
        # Correct username and password, but user is not activated
        form = LoginForm(email=user.email, password='example')
        assert form.validate() is False
        assert 'User account is not activated' in form.email.errors


class TestAddressForm:
    """Test all the address form features"""

    def test_new_form(self, app):
        empty_form = AddressForm()
        assert empty_form.validate() is False

    def test_minimal_form(self, app):
        form = AddressForm(
            name="Sharoon Thomas",
            is_minimal=True,
        )
        assert form.validate()
        assert form.country_id is None
        assert form.subdivision_id is None

    def test_complete_form(self, app):
        form = AddressForm(
            name="Sharoon Thomas",
            street="444 Castro St.",
            streetbis ="STE 1200",
            city="Mountain view",
            country="US",
            subdivision="CA",
            zip="94040",
        )
        assert form.validate()
        assert form.country_id is not None
        assert form.subdivision_id is not None

    def test_wrong_state(self, app):
        form = AddressForm(
            name="Sharoon Thomas",
            street="444 Castro St.",
            streetbis ="STE 1200",
            city="Mountain view",
            country="US",
            subdivision="XX",
            zip="94040",
        )
        assert form.validate() is False
        assert form.country_id is not None
        assert form.subdivision_id is None

    def test_without_country(self, app):
        form = AddressForm(
            name="Sharoon Thomas",
            street="444 Castro St.",
            streetbis ="STE 1200",
            city="Mountain view",
            country="XX",
            subdivision="CA",
            zip="94040",
        )
        assert form.validate() is False
        assert form.country_id is None
        assert form.subdivision_id is None

    def test_address_update(self, app, user):
        address = Address({
            'party': user.party.id,
            'name': 'Darth Vader',
        })
        address.save()
        form = AddressForm()
        form.process(
            name="Sharoon Thomas",
            street="444 Castro St.",
            streetbis ="STE 1200",
            city="Mountain view",
            country="US",
            subdivision="CA",
            zip="94040",
        )
        form.validate()
        assert not form.errors
        form.populate(address)
        assert address.name == "Sharoon Thomas"
        assert address.street == form.street.data
        assert address.streetbis == form.streetbis.data
        assert address.city == form.city.data
        assert address.zip == form.zip.data
        assert address.country.code == form.country.data
        assert address.subdivision.code == form.subdivision.data
        address.save()

        address_again = Address.get_by_id(address.id)
        assert address_again.name == "Sharoon Thomas"
        assert address_again.street == form.street.data
        assert address_again.streetbis == form.streetbis.data
        assert address_again.city == form.city.data
        assert address_again.zip == form.zip.data
        assert address_again.country.code == form.country.data
        assert address_again.subdivision.code == form.subdivision.data

        # Load the form with this record and check if defaults are set
        form = AddressForm(obj=address_again)
        assert form.name.data == address_again.name
        assert form.country.data == address_again.country.code
        assert form.subdivision.data == address_again.subdivision.code

        # Finally delete the address
        address_again.delete()
