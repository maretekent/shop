# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
import pytest
from flask import url_for
from shop.cart.models import Cart
from shop.globals import current_channel
from shop.product.models import Product
from shop.user.models import User


@pytest.fixture
def active_user(app):
    """Create an active user for testing."""
    user = User.query.filter_by_domain(
        [('email', 'ilike', 'func@bar.com')]
    ).first()

    if user:
        return user

    # Record does not exist. So create.
    user = User(
        name='John Doe',
        email='func@bar.com',
        password='myprecious',
        active=True
    )
    return user.save()


class TestLoggingIn:
    """Login."""

    def test_can_log_in_returns_200(self, active_user, testapp):
        """Login successful."""
        # Goes to login page
        res = testapp.get('/login')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_sees_alert_on_log_out(self, active_user, testapp):
        """Show alert on logout."""
        res = testapp.get('/login')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        res = testapp.get(url_for('public.logout')).follow()
        # sees alert
        assert 'You are logged out.' in res

    def test_sees_error_message_if_password_is_incorrect(
            self, active_user, testapp):
        """Show error if password is incorrect."""
        # Goes to login
        res = testapp.get('/login')
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'wrong'
        # Submits
        res = form.submit()
        # sees error
        assert 'Invalid password' in res

    def test_sees_error_message_if_username_doesnt_exist(
            self, active_user, testapp):
        """Show error if username doesn't exist."""
        # Goes to login
        res = testapp.get('/login')
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['email'] = 'unknown@email.com'
        form['password'] = 'myprecious'
        # Submits
        res = form.submit()
        # sees error
        assert 'Unknown email' in res


class TestRegistering:
    """Register a user."""

    @pytest.mark.usefixtures('delete_foo2')
    def test_can_register(self, testapp):
        """Register a new user."""
        old_count = User.query.count()

        # Goes to register page
        res = testapp.get(url_for('public.register'))

        # Fills out the form
        form = res.forms['registerForm']
        form['name'] = 'John Doe'
        form['email'] = 'foo2@bar.com'
        form['password'] = 'secret'
        form['confirm'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

        # A new user was created
        assert User.query.count() == old_count + 1

    def test_sees_error_message_if_passwords_dont_match(
            self, active_user, testapp):
        """Show error if passwords don't match."""
        # Goes to registration page
        res = testapp.get(url_for('public.register'))
        # Fills out form, but passwords don't match
        form = res.forms['registerForm']
        form['name'] = 'John Doe'
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['confirm'] = 'secrets'
        # Submits
        res = form.submit()
        # sees error message
        assert 'Passwords must match' in res

    def test_sees_error_message_if_user_already_registered(
            self, active_user, testapp):
        """Show error if user already registered."""
        # Goes to registration page
        res = testapp.get(url_for('public.register'))

        # Fills out form, but username is already registered
        form = res.forms['registerForm']
        form['name'] = 'John Doe'
        form['email'] = active_user.email
        form['password'] = 'secret'
        form['confirm'] = 'secret'

        # Submits
        res = form.submit()
        # sees error
        assert 'Email already registered' in res


class TestAddingToCart:
    """Add to cart"""

    def test_guest_user_adds_to_cart(self, testapp):
        """Guest user adds product to cart"""
        res = testapp.get('/')
        cart = Cart.query.filter_by_domain([
            ('sessionid', '=', testapp.cookies['session'])
        ]).first()
        assert cart is None

        # Goes to product page
        product = Product.query.filter_by_domain([
            ('channel_listings.channel', '=', current_channel.id),
        ]).first()
        res = testapp.get('/products/%s' % product.listing.product_identifier)

        # Submits form by clicking Add to Cart button
        form = res.forms['add-to-cart']
        res = form.submit().follow()

        assert res.status_code == 200

        cart = Cart.query.filter_by_domain([
            ('sessionid', '=', testapp.cookies['session'])
        ]).first()
        assert cart.is_empty is False
        assert cart.size == 1

    def test_registered_user_adds_to_cart(self, active_user, testapp):
        """Registered user adds to cart"""
        res = testapp.get('/')
        cart = Cart.query.filter_by_domain([
            ('sessionid', '=', testapp.cookies['session'])
        ]).first()
        assert cart is None

        # User logs in
        res = testapp.get('/login')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

        # Goes to product page
        product = Product.query.filter_by_domain([
            ('channel_listings.channel', '=', current_channel.id),
        ]).first()
        res = testapp.get('/products/%s' % product.listing.product_identifier)

        # Submits form by clicking Add to Cart button
        form = res.forms['add-to-cart']
        res = form.submit().follow()

        assert res.status_code == 200

        cart = Cart.query.filter_by_domain([
            ('user', '=', active_user.id)
        ]).first()
        assert cart.is_empty is False
        assert cart.size == 1
        assert cart.sale.party == active_user.party

    def test_add_items_to_cart_from_guest_cart_on_sign_in(self, active_user, testapp):
        """
        On sign in user's cart should have
        items added as a guest
        """
        # Guest user adds product to cart
        res = testapp.get('/')
        cart = Cart.query.filter_by_domain([
            ('sessionid', '=', testapp.cookies['session'])
        ]).first()
        assert cart is None

        # Goes to product page
        product = Product.query.filter_by_domain([
            ('channel_listings.channel', '=', current_channel.id),
        ]).first()
        res = testapp.get('/products/%s' % product.listing.product_identifier)

        # Submits form by clicking Add to Cart button
        form = res.forms['add-to-cart']
        res = form.submit().follow()

        assert res.status_code == 200

        cart = Cart.query.filter_by_domain([
            ('sessionid', '=', testapp.cookies['session'])
        ]).first()
        assert cart.is_empty is False
        assert cart.size == 1

        # User logs in
        res = testapp.get('/login')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

        user_cart = Cart.query.filter_by_domain(
            [
                ('user', '=', active_user.id)
            ]
        ).first()
        assert user_cart.is_empty is False
        assert user_cart.size == 1
