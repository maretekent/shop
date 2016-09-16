# -*- coding: utf-8 -*-
"""Checkout Models"""
import functools

from flask import redirect, url_for
from fulfil_client.model import ModelType, StringType
from shop.fulfilio import Model
from shop.globals import current_cart, current_channel


def not_empty_cart(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        cart = current_cart
        if cart.is_empty:
            return redirect(url_for('cart.view_cart'))
        return function(*args, **kwargs)
    return wrapper


def sale_has_non_guest_party(function):
    """
    Ensure that the sale has a party who is not guest.
    The sign-in method authomatically changes the party to a party based on the
    session.
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        cart = current_cart
        if cart.sale and cart.sale.party and \
                cart.sale.party.id == current_channel.anonymous_customer.id:
            return redirect(url_for('checkout.sign_in'))
        return function(*args, **kwargs)
    return wrapper


class PaymentGateway(Model):
    __model_name__ = 'payment_gateway.gateway'

    provider = StringType()
    stripe_api_key = StringType()
    stripe_publishable_key = StringType()


class PaymentProfile(Model):
    __model_name__ = 'party.payment_profile'

    party = ModelType('party.party')
