# -*- coding: utf-8 -*-
"""User forms."""
from flask import request
from flask_login import current_user
from flask_wtf import Form
from shop.public.models import Country, Subdivision
from shop.user.models import User
from wtforms import PasswordField, SelectField, StringField, BooleanField
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
        if 'choices' not in kwargs:
            kwargs['choices'] = self.get_choices()
        super(CountrySelectField, self).__init__(*args, **kwargs)

    def get_choices(self):
        return [
            (country.code, country.name)
            for country in Country.get_list()
        ]

    def process_data(self, country):
        """
        Process the Python data applied to this field and
        store the result.

        This will be called during form construction by the form’s
        kwargs or obj argument.
        """
        if isinstance(country, Country):
            self.data = country.code
        else:
            self.data = country


class SubdivisionSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        super(SubdivisionSelectField, self).__init__(*args, **kwargs)
        self.choices = []

    def process_data(self, subdivision):
        """
        Process the Python data applied to this field and
        store the result.

        This will be called during form construction by the form’s
        kwargs or obj argument.
        """
        if isinstance(subdivision, Subdivision):
            self.data = subdivision.code
        else:
            self.data = subdivision

    def pre_validate(self, form):
        if form.country.data is None:
            return None
        country = Country.from_code(form.country.data)
        if not country:
            raise ValidationError(
                "Country code is not valid."
            )
        subdivision = country.get_subdivision(self.data)
        if not subdivision:
            raise ValidationError(
                "Subdivision is not valid for the selected country."
            )


class RequiredIf(DataRequired):
    def __init__(self, field_name, field_value=True, *args, **kwargs):
        self.field_name = field_name
        self.field_value = field_value
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.field_name)
        if other_field is None:
            raise Exception(
                'no field named "%s" in form' % self.field_name
            )
        if other_field.data == self.field_value:
            super(RequiredIf, self).__call__(form, field)


class AddressForm(Form):
    name = StringField(
        'Name',
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. John Doe"}
    )
    is_minimal = BooleanField('Is minimal address ?', default=False)
    street = StringField(
        'Address Line 1',
        validators=[RequiredIf('is_minimal', False)],
        render_kw={"placeholder": "Street address, P.O. box, company name, c/o"}
    )
    streetbis = StringField(
        'Address Line 2',
        render_kw={"placeholder": "Apartment, suite, unit, building, floor, etc."}
    )
    zip = StringField(
        'Post Code',
        validators=[RequiredIf('is_minimal', False)],
        render_kw={"placeholder": "e.g. 560100"}
    )
    city = StringField(
        'City',
        validators=[RequiredIf('is_minimal', False)],
        render_kw={"placeholder": "e.g. Los Angeles, Beverly Hills."}
    )
    country = CountrySelectField(
        'Country',
        validators=[RequiredIf('is_minimal', False)],
        coerce=unicode
    )
    subdivision = SubdivisionSelectField(
        'State/Province/Region',
        validators=[RequiredIf('is_minimal', False)],
        coerce=unicode
    )
    phone = StringField(
        'Phone',
        render_kw={"placeholder": "e.g. +1234556"}
    )

    @property
    def country_id(self):
        if not self.country.data:
            return
        country = Country.from_code(self.country.data)
        if country:
            return country.id

    @property
    def subdivision_id(self):
        if not self.subdivision.data:
            return
        country = Country.from_code(self.country.data)
        if not country:
            return
        subdivision = country.get_subdivision(self.subdivision.data)
        if subdivision:
            return subdivision.id

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
        if ip_address is None:
            return
        match = geolite2.lookup(ip_address)
        country_code = 'US'
        if match is not None:
            country_code = match.country or 'US'
        return country_code

    def __init__(self, *args, **kwargs):
        if 'country' not in kwargs:
            kwargs['country'] = self.guess_country_code()
        super(AddressForm, self).__init__(*args, **kwargs)

    def populate(self, address):
        """
        Populate the given address model instance with data
        from the form.
        """
        for field in ['name', 'street', 'streetbis', 'zip', 'city', 'phone']:
            setattr(address, field, getattr(self, field).data)
        address.country = self.country_id
        address.subdivision = self.subdivision_id


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
