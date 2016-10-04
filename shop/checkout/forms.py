# -*- coding: utf-8 -*-
"""Checkout forms."""
from flask_login import current_user
from flask_wtf import Form

from shop.checkout.models import PaymentProfile
from shop.user.forms import AddressForm
from shop.user.models import Address
from wtforms import IntegerField, PasswordField, RadioField, StringField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError


class CheckoutSignInForm(Form):
    """Checkout SignIn Form"""

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    checkout_mode = RadioField(
        'Checkout Mode', choices=[
            ('guest', 'Checkout as a guest'),
            ('account', 'Use my account'),
        ]
    )

    def validate_password(self, field):
        if self.checkout_mode.data == 'account' and not field.data:
            raise ValidationError('Password is required.')


class CheckoutAddressForm(AddressForm):
    """Checkout Address Form"""

    address = IntegerField("Address")

    def validate(self):
        """Validate the form."""
        if current_user.is_anonymous or not self.address.data:
            return super(CheckoutAddressForm, self).validate()

        address_exist = Address.query.filter_by_domain([
            ('party', '=', current_user.party.id),
            ('id', '=', self.address.data)
        ]).first()
        if address_exist:
            return True
        return False


class CheckoutPaymentForm(Form):
    """
    Checkout payment form
    """
    payment_profile_id = IntegerField('Payment profile')
    stripe_token = StringField('Stripe Token')

    def validate(self):
        initial_validation = super(CheckoutPaymentForm, self).validate()

        if not initial_validation:
            return False

        if current_user.is_anonymous and self.payment_profile_id.data:
            self.payment_profile_id.errors.append("A payment profile cannot belong to a guest user")
            return False

        if not current_user.is_anonymous and self.payment_profile_id.data:
            payment_profile = PaymentProfile.get_by_id(self.payment_profile_id.data)
            if payment_profile.party != current_user.party:
                return False
        return True