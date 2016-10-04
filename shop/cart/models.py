# -*- coding: utf-8 -*-
"""Product models."""
import functools
from datetime import date

from flask import session
from flask_login import current_user, user_logged_in
from fulfil_client.model import (Date, FloatType, ModelType, MoneyType,
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

    _eager_fields = set(['sale.currency.code'])

    product = ModelType("product.product")
    quantity = FloatType()
    unit = ModelType("product.uom")
    unit_price = MoneyType('currency_code')
    amount = MoneyType('currency_code')
    description = StringType()
    delivery_address = ModelType('party.address')
    shipping_date = Date()

    @property
    def currency_code(self):
        return self._values.get('sale.currency.code')

    def update_shipping_address(self, address_id):
        self.delivery_address = address_id
        self.save()

    def update_shipping_date(self, shipping_date):
        self.shipping_date = shipping_date
        self.save()


class Sale(Model):
    __model_name__ = 'sale.sale'

    _eager_fields = set(['currency.code'])

    number = StringType()
    party = ModelType("party.party")
    shipment_address = ModelType("party.address")
    invoice_address = ModelType("party.address")
    total_amount = MoneyType('currency_code')
    tax_amount = MoneyType('currency_code')
    untaxed_amount = MoneyType('currency_code')
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

    @property
    def currency_code(self):
        return self._values.get('currency.code')

    def add_product(self, product_id, quantity, shipping_date, address_id):
        # check if SaleLine already exists
        sale_line = SaleLine.query.filter_by_domain([
            ('product', '=', product_id),
            ('sale', '=', self.id),
            ('shipping_date', '=', shipping_date),
            ('delivery_address', '=', address_id)
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
                'warehouse': current_channel.warehouse,
                'delivery_address': address_id,

                # XXX: Find better way to set default delivery date
                'shipping_date': shipping_date or date.today(),
            }
            line_data.update(SaleLine.rpc.on_change_product(line_data))
            if line_data.get('taxes'):
                line_data['taxes'] = [('add', line_data.get('taxes'))]
            sale_line = SaleLine(**{
                k: v for k, v in line_data.iteritems()
                if '.' not in k
            }).save()

        return sale_line


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
        guest_cart = Cart.find_cart(None)
        if guest_cart and guest_cart.sale and guest_cart.sale.lines:
            # Active cart is user's cart
            user_cart = Cart.get_active()
            # Transfer lines from guest cart to user cart
            for line in guest_cart.sale.lines:
                user_cart.add_product(line.product.id, line.quantity)
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
    def get_active(cls):
        """
        Get active cart for either a user or a guest
        Or create one if none found
        """
        domain = [
            ('sessionid', '=', session.sid)
        ]
        if not current_user.is_anonymous:
            domain = [
                ('user', '=', current_user.id)
            ]
        cart = Cart.query.filter_by_domain(domain).first()
        if not cart:
            if current_user.is_anonymous:
                cart = Cart(sessionid=session.sid).save()
            else:
                cart = Cart(user=current_user.id).save()

        return cart

    @classmethod
    def find_cart(cls, user_id=None):
        """
        Return the cart for the user if one exists. The user is None a guest
        cart for the session is found.

        :param user: ID of the user
        :return: Active record of cart or None
        """
        domain = [
            ('user', '=', user_id)
        ]
        if not user_id:
            domain.append(('sessionid', '=', session.sid))
        cart = Cart.query.filter_by_domain(domain).first()
        return cart

    @require_cart_with_sale
    def add_product(
            self, product_id, quantity, shipping_date=None, address_id=None
    ):
        self.refresh()
        self.sale.add_product(product_id, quantity, shipping_date, address_id)

    def remove_sale_line(self, line_id):
        self.refresh()
        SaleLine.rpc.delete([line_id])

    def clear(self):
        self.sale = None
        self.save()

    @require_cart_with_sale
    def update_shipping_address(self, line_id, address_id):
        line = SaleLine.get_by_id(line_id)
        line.update_shipping_address(address_id)

    @require_cart_with_sale
    def update_shipping_date(self, line_id, shipping_date):
        line = SaleLine.get_by_id(line_id)
        line.update_shipping_date(shipping_date)
