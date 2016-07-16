# -*- coding: utf-8 -*-
"""Product models."""
from flask import current_app

from shop.fulfilio import CurrencyType, Model, StringType
from shop.utils import get_random_product


class ProductTemplate(Model):

    __model_name__ = 'product.template'

    name = StringType()

    @property
    def listings(self):
        """
        Return the products (that are listed in the current channel) and
        active.
        """
        listings = ChannelListing.query.filter_by_domain(
            [
                ('channel', '=', current_app.config['FULFIL_CHANNEL']),
                ('state', '=', 'active'),
                ('product.template', '=', self.id),
            ],
        ).all()
        return listings


class Product(Model):

    __model_name__ = 'product.product'

    _eager_fields = set(['variant_name', 'media', 'default_image.url'])

    code = StringType()
    list_price = CurrencyType()
    description = StringType()
    long_description = StringType()
    uri = StringType()

    @property
    def image(self):
        return self._values.get('default_image.url')

    @property
    def name(self):
        return self._values['variant_name']

    def get_related_products(self):
        """
        Return relsted products of this product
        """
        return [
            get_random_product() for c in range(5)
        ]


class ChannelListing(Model):
    __model_name__ = 'product.product.channel_listing'

    _eager_fields = set(['channel', 'product', 'product.template'])

    product_identifier = StringType()
    state = StringType()

    @classmethod
    def from_slug(cls, slug):
        return cls.query.filter_by_domain(
            [
                ('channel', '=', current_app.channel),
                ('product_identifier', '=', slug),
            ]
        ).first()

    @property
    def channel(self):
        return self._values['channel']

    @property
    def template(self):
        return ProductTemplate.from_cache(
            id=self._values['product.template'], refresh=True
        )

    @property
    def product(self):
        return Product.from_cache(id=self._values['product'])

    @property
    def unit_price(self):
        # TODO: Price should come from the listing and customer
        return self.product.list_price
