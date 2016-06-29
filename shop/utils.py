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


def dummy_products(func):
    def wrapper(*args, **kwargs):
        import random
        from shop.product.models import Product
        p_images = [
            "https://cdn.shopify.com/s/files/1/0533/3153/products/1-1_large.jpg?v=1404837242",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2405/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/682/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2357/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2356/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/386/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/388/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        ]
        dummy_products = [
            Product(name='Product 1', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 2', price="$40.00", image=random.choice(p_images)),
            Product(name='Product long one 3', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 4', price="$140.00", image=random.choice(p_images)),
            Product(name='Product 5', price="$10,040.00", image=random.choice(p_images)),
            Product(name='Product 6', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product longer longer 7', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 8', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 9', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 10', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 11', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 12', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 13', price="$1,040.00", image=random.choice(p_images)),
            Product(name='Product 14', price="$1,040.00", image=random.choice(p_images)),
        ]
        return dummy_products
    return wrapper
