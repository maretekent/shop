# -*- coding: utf-8 -*-
"""Product models."""
import functools

from flask import session
from flask_login import current_user, user_logged_in
from fulfil_client.model import (Date, DecimalType, FloatType, ModelType,
                                 One2ManyType, StringType)
from shop.fulfilio import Model, ShopQuery
from shop.globals import current_channel


def require_cart_with_sale(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        cart = Cart.get_active()
        if not cart.sale:
            if current_user.is_anonymous:
                party = current_channel.anonymous_customer
            else:
                party = current_user.party
            sale_data = {
                "party": party.id,
                "invoice_address": None,
                "shipment_address": None,
                "company": current_channel.company,
                "currency": current_channel.currency,
                "is_cart": True,
                "channel": current_channel.id,
            }
            sale_data.update(Sale.rpc.on_change_channel(sale_data))
            sale = Sale(**{
                k: v for k, v in sale_data.iteritems()
                if '.' not in k
            }).save()
            cart.sale = sale.id
            cart.save()
        return function(*args, **kwargs)
    return wrapper


class SaleLine(Model):
    __model_name__ = 'sale.line'

    product = ModelType("product.product")
    quantity = FloatType()
    unit_price = DecimalType()
    amount = DecimalType()
    description = StringType()


class Sale(Model):
    __model_name__ = 'sale.sale'

    number = StringType()
    party = ModelType("party.party")
    shipment_address = ModelType("party.address")
    invoice_address = ModelType("party.address")
    total_amount = DecimalType()
    tax_amount = DecimalType()
    untaxed_amount = DecimalType()
    lines = One2ManyType("sale.line")
    invoices = One2ManyType("account.invoice")
    sale_date = Date()
    state = StringType()
    currency = StringType()

    #: This access code will be cross checked if the user is guest for a match
    #: to optionally display the order to an user who has not authenticated
    #: as yet
    guest_access_code = StringType()

    @classmethod
    def get_shop_query(cls):
        return ShopQuery(cls.rpc, cls)

    def add_product(self, product_id, quantity):
        # check if SaleLine already exists
        sale_line = SaleLine.query.filter_by_domain([
            ('product', '=', product_id),
            ('sale', '=', self.id),
        ]).first()
        if sale_line:
            sale_line.quantity = quantity
            sale_line.save()
        else:
            line_data = {
                'sale': self.id,
                'product': product_id,
                'quantity': quantity,
                '_parent_sale.shipment_address': self.shipment_address and
                self.shipment_address.id,
                '_parent_sale.channel': current_channel.id,
                '_parent_sale.party': current_channel.anonymous_customer.id,
                '_parent_sale.currency': current_channel.currency,
                'warehouse': current_channel.warehouse
            }
            line_data.update(SaleLine.rpc.on_change_product(line_data))
            if line_data.get('taxes'):
                line_data['taxes'] = [('add', line_data.get('taxes'))]
            SaleLine(**{
                k: v for k, v in line_data.iteritems()
                if '.' not in k
            }).save()


class Cart(Model):
    __model_name__ = 'nereid.cart'

    sessionid = StringType()
    sale = ModelType("sale.sale")
    user = ModelType("nereid.user")

    @staticmethod
    @user_logged_in.connect
    def update_user_cart(sender, user):
        """This method is triggered when a login event occurs.
        When a user logs in, all items in his guest cart should be added to his
        logged in or registered cart. If there is no such cart, it should be
        created.
        """
        # There is a cart
        guest_cart = Cart.query.filter_by_domain(
            [
                ('sessionid', '=', session.sid)
            ]
        ).first()
        if guest_cart and guest_cart.sale and guest_cart.sale.lines:
            user_cart = Cart.get_active(user=user)
            # Transfer lines from guest cart to user cart
            for line in guest_cart.sale.lines:
                user_cart.sale.add_product(line.product.id, line.quantity)

        # Clear the old cart
        guest_cart.clear()

    def confirm(self):
        "Move order to confirmation state"
        sale = self.sale
        Sale.rpc.quote([sale.id])
        Sale.rpc.confirm([sale.id])

        # TODO: Set sale_date to today
        self.sale = None
        self.save()

    @property
    def size(self):
        # TODO: Assuming every item has same unit
        if self.is_empty:
            return 0
        return sum(map(lambda l: l.quantity, self.sale.lines))

    @property
    def is_empty(self):
        if not self.sale:
            return True
        if len(self.sale.lines) == 0:
            return True
        return False

    @classmethod
    def get_active(cls, user=current_user):
        """
        Get active cart for either a user or a guest
        Or create one if none found
        """
        if user.is_anonymous:
            cart = Cart.query.filter_by_domain(
                [
                    ['sessionid', '=', session.sid],
                ]
            ).first()
            if not cart:
                cart = Cart(sessionid=session.sid).save()
        else:
            cart = Cart.query.filter_by_domain(
                [
                    ('user', '=', user.id)
                ]
            ).first()
            if not cart:
                cart = Cart(user=user.id).save()

        return cart

    @require_cart_with_sale
    def add_product(self, product_id, quantity):
        self.refresh()
        self.sale.add_product(product_id, quantity)

    def remove_sale_line(self, line_id):
        self.refresh()
        SaleLine.rpc.delete([line_id])

    def clear(self):
        self.sale = None
        self.save()
