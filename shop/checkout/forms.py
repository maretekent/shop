# -*- coding: utf-8 -*-
"""Checkout forms."""
from flask_login import current_user
from flask_wtf import Form
from shop.user.forms import AddressForm
from shop.user.models import Address
from wtforms import IntegerField, PasswordField, RadioField, StringField
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
