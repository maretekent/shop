# -*- coding: utf-8 -*-
"""Checkout forms."""
from flask_wtf import Form
from wtforms import PasswordField, RadioField, StringField
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
