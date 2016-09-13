# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
import pytest
from flask import url_for
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


@pytest.skip('Not implemented login yet')
class TestLoggingIn:
    """Login."""

    def test_can_log_in_returns_200(self, active_user, testapp):
        """Login successful."""
        # Goes to homepage
        res = testapp.get('/')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = active_user.email
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_sees_alert_on_log_out(self, active_user, testapp):
        """Show alert on logout."""
        res = testapp.get('/')
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
        # Goes to homepage
        res = testapp.get('/')
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
        # Goes to homepage
        res = testapp.get('/')
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

        # Goes to homepage
        res = testapp.get('/')

        # Clicks Create Account button
        res = res.click('Create account')

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
