# -*- coding: utf-8 -*-
"""User models."""
from flask import current_app, url_for
from flask_babel import gettext
from flask_login import UserMixin
from itsdangerous import TimestampSigner, URLSafeSerializer

from fulfil_client.model import BooleanType, ModelType, StringType
from shop.extensions import fulfil
from shop.fulfilio import Model, channel
from shop.utils import render_email


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

    name = StringType(required=True)
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
            party = Party(name=self.name)
            party.save()
            self.party = party.id
        super(User, self).save()

    @classmethod
    def user_exists(cls, email):
        """Check if the user exists"""
        return cls.query.filter_by_domain(
            [('email', 'ilike', email)]
        ).show_active_only(False).exists()

    @staticmethod
    def _signer():
        return TimestampSigner(current_app.secret_key)

    @staticmethod
    def _serializer():
        return URLSafeSerializer(current_app.secret_key)

    def _get_sign(self, salt):
        """
        Returns a timestampsigned, url_serialized sign  with a salt
        'verification'.
        """
        return self._signer().sign(self._serializer().dumps(self.id, salt=salt))

    def get_email_verification_link(self, **options):
        """
        Returns an email verification link for the user
        """
        return url_for(
            'public.verify_email',
            sign=self._get_sign('verification'),
            user_id=self.id,
            **options
        )

    def get_activation_link(self, **options):
        """
        Returns an activation link for the user
        """
        return url_for(
            'public.activate',
            sign=self._get_sign('activation'),
            user_id=self.id,
            **options
        )

    def get_reset_password_link(self, **options):
        """
        Returns a password reset link for the user
        """
        return url_for(
            'public.new_password',
            sign=self._get_sign('reset-password'),
            user_id=self.id,
            **options
        )

    def initiate_reset_password(self):
        "Initiate the password reset for the user"
        EmailQueue = fulfil.model('email.queue')

        email_message = render_email(
            channel.support_email,      # From
            self.email,                 # To
            gettext('Your %(channel)s password', channel=channel.name), # Subj
            'emails/reset-password.text',
            'emails/reset-password.html',
            user=self,
        )
        EmailQueue.create([{
            'from_addr': channel.support_email,
            'to_addrs': self.email,
            'msg': email_message.as_string(),
        }])
