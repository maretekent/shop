# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import Factory, Sequence

from shop.user.models import User


class ModelFactory(Factory):
    class Meta:
        abstract = True  # Optional, but explicit.

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class(kwargs)


class UserFactory(ModelFactory):
    """User factory."""

    name = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = 'example'
    active = True

    class Meta:
        """Factory configuration."""

        model = User
