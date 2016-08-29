# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import pytest
from webtest import TestApp

from shop.app import create_app
from shop.settings import TestConfig
from shop.user.models import User

from .factories import UserFactory


@pytest.yield_fixture(scope='function')
def app():
    """An application for the tests."""
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='function')
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture
def user(app):
    """A user for the tests."""
    user = User.query.filter_by_domain(
        [('email', 'ilike', 'foo@bar.com')]
    ).show_active_only(False).first()

    if user:
        return user

    # Record does not exist. So create.
    user = UserFactory(
        display_name="John Doe",
        email='foo@bar.com',
        password='myprecious'
    )
    user.save()
    return user


@pytest.fixture(scope="function")
def delete_foo2(app):
    "Delete foo2@bar.com before test"
    User.query.filter_by(
        email='foo2@bar.com'
    ).show_active_only(False).delete()
