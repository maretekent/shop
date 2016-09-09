# -*- coding: utf-8 -*-
"""Product models."""
import functools

from flask import session, current_app
from shop.fulfilio import Model
from fulfil_client.model import StringType, ModelType, FloatType, DecimalType, \
    One2ManyType
from shop.product.models import Product
from shop.user.models import Address
from shop.globals import current_channel

def require_cart_with_sale(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        cart = Cart.get_active()
        if not cart.sale:
            sale = Sale(
                party=current_channel.anonymous_customer,
                invoice_address=None,
                shipment_address=None,
                company=current_channel.company,
                currency=current_channel.currency,
                is_cart=True,
                channel=current_channel.id,
            ).save()
            cart.sale = sale.id
            cart.save()
        return function(*args, **kwargs)
    return wrapper

class SaleLine(Model):
    __model_name__ = 'sale.line'

    product = ModelType(model=Product)
    quantity = FloatType()
    unit_price = DecimalType()
    amount = DecimalType()

class Sale(Model):
    __model_name__ = 'sale.sale'

    shipment_address = ModelType(model=Address)
    total_amount = DecimalType()
    tax_amount = DecimalType()
    untaxed_amount = DecimalType()
    lines = One2ManyType(model=SaleLine)

    def add_product(self, product_id, quantity):
        line_data = {
            'sale': self.id,
            'product': product_id,
            'quantity': quantity,
            '_parent_sale.shipment_address': self.shipment_address and \
                self.shipment_address.id,
            '_parent_sale.channel': current_channel.id,
            '_parent_sale.party': current_channel.anonymous_customer,
            '_parent_sale.currency': current_channel.currency,
            'warehouse': current_channel.warehouse
        }
        line_data.update(SaleLine.rpc.on_change_product(line_data))
        res = SaleLine(**{
            k: v for k, v in line_data.iteritems()
            if '.' not in k
        }).save()

class Cart(Model):
    __model_name__ = 'nereid.cart'

    sessionid = StringType()
    sale = ModelType(model=Sale)

    @property
    def size(self):
        # TODO: Assuming every item has same unit
        if self.is_empty:
            return 0
        return sum(map(lambda l: l.quantity, self.lines))

    @property
    def is_empty(self):
        if not self.sale:
            return True
        if len(self.lines) == 0:
            return True
        return False

    @classmethod
    def get_active(cls):
        """Always return a cart
        TODO: Make it work for logged in user
        """
        cart = Cart.query.filter_by_domain(
            [
                ['sessionid', '=', session.sid],
            ]
        ).first()
        if not cart:
            cart = Cart(sessionid=session.sid).save()
        return cart

    @require_cart_with_sale
    def add_product(self, product_id, quantity):
        self.refresh()
        self.sale.add_product(product_id, quantity)