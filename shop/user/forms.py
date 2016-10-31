# -*- coding: utf-8 -*-
"""User forms."""
from flask import request
from flask_login import current_user
from flask_wtf import Form
from shop.public.models import Country
from shop.user.models import User
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                ValidationError)
from geoip import geolite2


class RegisterForm(Form):
    name = StringField(
        'Full Name',
        validators=[DataRequired()]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    confirm = PasswordField(
        'Verify password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()

        if not initial_validation:
            return False

        if User.user_exists(self.email.data):
            self.email.errors.append('Email already registered')
            return False

        return True


class CountrySelectField(SelectField):
    def __init__(self, *args, **kwargs):
        super(CountrySelectField, self).__init__(*args, **kwargs)
        self.choices = [
            (country.id, country.name)
            for country in Country.get_list()
        ]

    # Override method in SelectField
    def process_data(self, country):
        self.data = country.id if country else None


class SubdivisionSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        super(SubdivisionSelectField, self).__init__(*args, **kwargs)
        self.choices = []

    # Override method in SelectField
    def process_data(self, subdivision):
        self.data = subdivision.id if subdivision else None

    def pre_validate(self, form):
        country = Country.from_cache(form.country.data)
        subdivisions = [s.id for s in country.subdivisions]
        if self.data not in subdivisions and len(subdivisions):
            raise ValidationError(
                "Subdivision is not valid for the selected country."
            )


class AddressForm(Form):
    name = StringField(
        'Name',
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. John Doe"}
    )
    street = StringField(
        'Address Line 1',
        validators=[DataRequired()],
        render_kw={"placeholder": "Street address, P.O. box, company name, c/o"}
    )
    streetbis = StringField(
        'Address Line 2',
        render_kw={"placeholder": "Apartment, suite, unit, building, floor, etc."}
    )
    zip = StringField(
        'Post Code',
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. 560100"}
    )
    city = StringField(
        'City',
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. Los Angeles, Beverly Hills."}
    )
    country = CountrySelectField(
        'Country',
        validators=[DataRequired()],
        coerce=int
    )
    subdivision = SubdivisionSelectField(
        'State/Province/Region',
        validators=[DataRequired()],
        coerce=int
    )
    phone = StringField(
        'Phone',
        render_kw={"placeholder": "e.g. +1234556"}
    )

    @classmethod
    def get_ip_address(cls):
        return request.environ.get(
            'HTTP_X_REAL_IP',
            request.headers.get(
                'X-Forwarded-For',
                request.remote_addr
            )
        )

    @classmethod
    def guess_country_code(cls):
        """
        Guess country from IP address
        """
        ip_address = cls.get_ip_address()
        match = geolite2.lookup(ip_address)
        country_code = 'US'
        if match is not None:
            country_code = match.country or 'US'
        return country_code

    @classmethod
    def guess_country_id(cls):
        code = cls.guess_country_code()
        if code:
            country = Country.from_code(code)
            return country


class ChangePasswordForm(Form):
    """Change Password form."""

    old_password = PasswordField(
        'Old Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Your old password"}
    )
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Your new password"}
    )
    confirm = PasswordField(
        'Verify New Password',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Type your new password again"}
    )

    def validate(self):
        """Validate the form."""
        initial_validation = super(ChangePasswordForm, self).validate()
        if not initial_validation:
            return False

        if not current_user.check_password(self.old_password.data):
            self.old_password.errors.append('Your old password is incorrect.')
            return False
        return True


class AccountForm(Form):
    """Change display name form."""

    name = StringField(
        'Your Name',
        validators=[DataRequired()],
        render_kw={"placeholder": "Your Name"}
    )

    email = StringField(
        'Email',
        render_kw={"placeholder": "Email"}
    )

    phone = StringField(
        'Phone Number',
        render_kw={"placeholder": "Phone"}
    )
