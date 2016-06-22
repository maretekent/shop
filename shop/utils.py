# -*- coding: utf-8 -*-
"""
Helper utilities and decorators.
"""
from flask import flash
from schematics.exceptions import ValidationError


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(
                getattr(form, field).label.text, error), category
            )


def is_email(value):
    """
    A schematics validator that checks if value is a valid email address.

    Email regex used to validate email formats. It simply asserts that
    one (and only one) @ exists in the given string. This is mainly
    to give user feedback and not to assert the e-mail validity.
    """
    if value.count('@') != 1:
        raise ValidationError(u'Invalid Email!')
    return value
