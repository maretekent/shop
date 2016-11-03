# -*- coding: utf-8 -*-
"""Product models."""
import functools
from datetime import date

from flask import session
from flask_login import current_user, user_logged_in
from fulfil_client.model import (Date, FloatType, ModelType, MoneyType,
                                 One2ManyType, StringType)
from flask_babel import format_number
from cached_property import cached_property
from shop.fulfilio import Model, ShopQuery
from shop.globals import current_channel, current_context


def require_cart_with_sale(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        cart = args[0]
        cart.sanitise()
        if not cart.sale:
            sale = Cart.create_sale()
            del cart.sale       # Delete cached property
            cart._values['sale'] = sale.id
            cart.save()
        return function(*args, **kwargs)
    return wrapper


class SaleLine(Model):
    __model_name__ = 'sale.line'

    _eager_fields = set(['sale.currency.code'])

    product = ModelType("product.product", cache=True)
    quantity = FloatType()
    unit = ModelType("product.uom", cache=True)
    unit_price = MoneyType('currency_code')
    amount = MoneyType('currency_code')
    description = StringType()
    delivery_address = ModelType('party.address')
    delivery_date = Date()
    gift_message = StringType()
    shipment_cost = MoneyType('currency_code')

    @property
    def currency_code(self):
        return self._values.get('sale.currency.code')

    def update_shipping_address(self, address_id):
        self.delivery_address = address_id
        self.save()

    def update_delivery_date(self, delivery_date):
        self.delivery_date = delivery_date
        self.save()

    def update_gift_message(self, gift_message):
        self.gift_message = gift_message
        self.save()

    def serialize(self):
        current_locale = current_context.get('language') or 'en_US'
        data = {
            'id': self.id,
            'product_id': self.product and self.product.id,
            'product': self.product and self.product.name or None,
            'product_identifier': self.product and self.product.listing and \
                self.product.listing.product_identifier,
            'quantity': format_number(self.quantity),
            'gift_message': self.gift_message or None,
            'unit': self.unit.symbol,
            'unit_price': self.unit_price.format(current_locale),
            'amount': self.amount.format(current_locale),
            'url': self.product and self.product.listing and \
                self.product.listing.get_absolute_url(),
            'image': self.product.image,
            'delivery_address': None,
            'is_shipping_line': True if self.shipment_cost else False
        }
        if self.delivery_address:
            data['delivery_address'] = self.delivery_address._values
        return data


class Sale(Model):
    __model_name__ = 'sale.sale'

    _eager_fields = set(['currency.code', 'lines'])

    number = StringType()
    party = ModelType("party.party")
    shipment_address = ModelType("party.address")
    invoice_address = ModelType("party.address")
    total_amount = MoneyType('currency_code')
    tax_amount = MoneyType('currency_code')
    untaxed_amount = MoneyType('currency_code')
    total_shipment_cost = MoneyType('currency_code')
    invoices = One2ManyType("account.invoice")
    sale_date = Date()
    state = StringType()
    currency = StringType()
    promo_code = StringType()

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

    @cached_property
    def lines(self):
        return SaleLine.query.filter_by_domain([
            ('sale', '=', self.id),
        ]).all()

    @cached_property
    def items_total(self):
        "Item total without tax and shipping"
        return self.untaxed_amount - self.total_shipment_cost

    def add_product(self, product_id, quantity, delivery_date, address_id):
        # check if SaleLine already exists
        sale_line = SaleLine.query.filter_by_domain([
            ('product', '=', product_id),
            ('sale', '=', self.id),
            ('delivery_date', '=', delivery_date),
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
                'delivery_date': delivery_date,
            }
            line_data.update(SaleLine.rpc.on_change_product(line_data))
            if line_data.get('taxes'):
                line_data['taxes'] = [('add', line_data.get('taxes'))]
            sale_line = SaleLine(**{
                k: v for k, v in line_data.iteritems()
                if '.' not in k
            }).save()

        return sale_line

    def prepare_for_payment(self):
        """Makes cart sale ready for payment.
        Helpful when you want to make sure shipping is properly applied
        before payment.
        """
        pass

    def apply_promo_code(self, promo_code):
        Sale.rpc.write([self.id], {'promo_code': promo_code})
        Sale.rpc.draft([self.id])
        Sale.rpc.apply_promotion([self.id])


class Cart(Model):
    __model_name__ = 'nereid.cart'

    _eager_fields = {'sale', }

    sessionid = StringType()
    user = ModelType("nereid.user")

    @cached_property
    def sale(self):
        if self._values.get('sale'):
            return Sale.get_by_id(self._values['sale'])

    @staticmethod
    @user_logged_in.connect
    def login_event_handler(sender, user):
        """This method is triggered when a login event occurs.
        When a user logs in, all items in his guest cart should be added to his
        logged in or registered cart. If there is no such cart, it should be
        created.
        """
        Cart._login_event_handler(sender, user)

    @classmethod
    def _login_event_handler(cls, sender, user):
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
        sale.sale_date = date.today()
        sale.save()

        Sale.rpc.quote([sale.id])
        Sale.rpc.confirm([sale.id])

        self.clear()

    @property
    def size(self):
        # TODO: Assuming every item has same unit
        if self.is_empty:
            return 0
        return sum(
            map(
                lambda l: l.quantity,
                filter(lambda l: not l.shipment_cost, self.sale.lines)
            )
        )

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

    @classmethod
    def create_sale(cls):
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
        return sale

    @require_cart_with_sale
    def add_product(
            self, product_id, quantity, delivery_date=None, address_id=None
    ):
        self.refresh()
        self.sale.add_product(product_id, quantity, delivery_date, address_id)

    def remove_sale_line(self, line_id):
        self.refresh()
        SaleLine.rpc.delete([line_id])

    def clear(self):
        Cart.rpc.write([self.id], {'sale': None})

    @require_cart_with_sale
    def update_shipping_address(self, line_id, address_id):
        line = SaleLine.get_by_id(line_id)
        line.update_shipping_address(address_id)

    @require_cart_with_sale
    def update_delivery_date(self, line_id, delivery_date):
        line = SaleLine.get_by_id(line_id)
        line.update_delivery_date(delivery_date)

    def update_gift_message(self, line_id, gift_message):
        line = SaleLine.get_by_id(line_id)
        line.update_gift_message(gift_message)

    def serialize(self):
        if not self.sale:
            return {
                'empty': True,
            }
        current_locale = current_context.get('language') or 'en_US'
        data = {
            'empty': self.is_empty,
            'size': self.size,
            'has_shipping': bool(self.sale.total_shipment_cost),
            'total_amount': self.sale.total_amount.format(current_locale),
            'tax_amount': self.sale.tax_amount.format(current_locale),
            'untaxed_amount': self.sale.untaxed_amount.format(current_locale),
            'untaxed_without_shipping': (
                self.sale.untaxed_amount - self.sale.total_shipment_cost
            ).format(current_locale),
            'total_shipment_cost': self.sale.total_shipment_cost.format(
                current_locale),
            'shipment_address': None,
        }
        data['lines'] = [
            line.serialize() for line in self.sale.lines
        ]
        if self.sale.shipment_address:
            data['shipment_address'] = self.sale.shipment_address._values
        return data

    def sanitise(self):
        """This method verifies that the cart is valid
        """
        if not self.sale:
            return
        if self.sale.state != 'draft':
            self.sale = None
        self.save()

    @require_cart_with_sale
    def apply_promo_code(self, promo_code):
        self.sale.apply_promo_code(promo_code)
