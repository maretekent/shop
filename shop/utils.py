# -*- coding: utf-8 -*-
"""
Helper utilities and decorators.
"""
from flask import flash, current_app
from flask.ext.themes2 import get_theme, render_theme_template as rtt


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(
                getattr(form, field).label.text, error), category
            )


def get_current_theme():
    """
    Return the identifier of the current theme.
    """
    ident = current_app.config.get('THEME', 'default')
    return get_theme(ident)


def render_theme_template(*args, **kwargs):
    """
    Render the template using current theme.
    """
    return rtt(get_current_theme(), *args, **kwargs)
