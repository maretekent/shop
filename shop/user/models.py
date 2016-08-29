# -*- coding: utf-8 -*-
"""User models."""
from flask_login import UserMixin

from fulfil_client.model import BooleanType, ModelType, StringType
from shop.fulfilio import Model


class Party(Model):
    """
    A contact (party) in Fulfil.

    Needed since every user is associated with a contact
    """

    __model_name__ = 'party.party'

    name = StringType(required=True)


class User(UserMixin, Model):
    """
    A user of the app.
    """

    __model_name__ = 'nereid.user'

    email = StringType(required=True)

    # TODO: This should be changed to name
    display_name = StringType(required=True)
    password = StringType()
    party = ModelType(model=Party)
    active = BooleanType()

    @property
    def is_active(self):
        "For Flask login"
        return self.active

    @classmethod
    def find_user(cls, email):
        """
        Find the user from the email
        """
        return cls.query.filter_by_domain(
            [('email', 'ilike', email)]
        ).show_active_only(False).first()

    def set_password(self, password):
        """Set password."""
        self.password = password
        self.save()

    def check_password(self, value):
        """Check password."""
        return self.rpc.match_password(self.id, value)

    def save(self):
        if not self.party:
            party = Party(name=self.display_name)
            party.save()
            self.party = party.id
        super(User, self).save()

    @classmethod
    def user_exists(cls, email):
        """Check if the user exists"""
        return cls.query.filter_by_domain(
            [('email', 'ilike', email)]
        ).show_active_only(False).exists()
