# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import Form
from wtforms import PasswordField, StringField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                ValidationError)

from shop.user.models import User


class LoginForm(Form):
    """Login form."""

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        self.user = User.find_user(self.email.data)
        if not self.user:
            self.email.errors.append('Unknown email')
            return False

        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        if not self.user.active:
            self.email.errors.append('User not activated')
            return False
        return True


class ResetPasswordForm(Form):
    "Initiates a password reset"

    email = StringField(
        'E-mail',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Your registered email"}

    )

    def validate_email(self, field):
        self.user = User.find_user(self.email.data)

        if not self.user:
            raise ValidationError('Unknown e-mail')


class NewPasswordForm(Form):
    """New Password form."""

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Password"}
    )
    confirm = PasswordField(
        'Verify password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Type password again"}
    )
