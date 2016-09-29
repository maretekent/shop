# -*- coding: utf-8 -*-
"""Product models."""
import json

from flask import url_for
from fulfil_client.model import (MoneyType, IntType, ModelType, One2ManyType,
                                 StringType)
from shop.fulfilio import Model, ShopQuery
from shop.globals import current_channel
from shop.utils import get_random_product


class ProductTemplate(Model):

    __model_name__ = 'product.template'

    name = StringType()
    variation_attributes = One2ManyType("product.variation_attributes")

    @property
    def listings(self):
        """
        Return the products (that are listed in the current channel) and
        active.
        """
        return ChannelListing.query.filter_by_domain(
            [
                ('channel', '=', current_channel.id),
                ('state', '=', 'active'),
                ('product.template', '=', self.id),
            ],
        ).all()

    def get_product_variation_data(self):
        """
        """
        self.refresh()
        variation_attributes = map(
            lambda variation: variation.serialize(),
            self.variation_attributes
        )
        variants = []
        for listing in self.listings:
            product = listing.product
            product.refresh()  # Fetch record again
            variant_data = product.serialize(purpose='variant_selection')
            availability = listing.get_availability()
            variant_data['inventory_status'] = availability['value']
            variant_data['attributes'] = {}
            for variation in self.variation_attributes:
                if variation.attribute.type_ == 'selection':
                    # Selection option objects are obviously not serializable
                    # So get the name
                    variant_data['attributes'][variation.attribute.id] = \
                        str(product.get_attribute_value(variation.attribute).id)
                else:
                    variant_data['attributes'][variation.attribute.name] = \
                        product.get_attribute_value(variation.attribute)
            variants.append(variant_data)

        rv = {
            'variants': variants,
            'variation_attributes': variation_attributes,
        }
        return json.dumps(rv)


class Product(Model):

    __model_name__ = 'product.product'

    _eager_fields = set([
        'template', 'variant_name', 'media', 'default_image.url'
    ])

    code = StringType()
    list_price = MoneyType('currency_code')
    description = StringType()
    long_description = StringType()
    uri = StringType()
    attributes = One2ManyType("product.product.attribute")
    media = One2ManyType("product.media")
    cross_sells = One2ManyType('product.product')

    @property
    def currency_code(self):
        return current_channel.currency_code

    @property
    def image(self):
        return self._values.get('default_image.url')

    @property
    def images(self):
        return map(lambda m: m.url, self.media)

    @property
    def name(self):
        return self._values['variant_name'] or self.template.name

    @property
    def template(self):
        return ProductTemplate.from_cache(self._values['template'])

    @property
    def listing(self):
        return ChannelListing.query.filter_by_domain(
            [
                ('product', '=', self.id),
                ('channel', '=', current_channel.id)
            ]
        ).first()

    def get_absolute_url(self):
        return url_for('products.product', handle=self.uri)

    def get_related_products(self):
        """
        Return relsted products of this product
        """
        return [
            get_random_product() for c in range(5)
        ]

    def get_attribute_value(self, attribute, silent=True):
        for product_attr in self.attributes:
            if product_attr.attribute == attribute:
                return getattr(
                    product_attr,
                    'value_%s' % attribute.type_
                )
        else:
            if silent:
                return True
            raise AttributeError(attribute.name)

    def serialize(self, purpose=None):
        return {
            'id': self.id,
            'rec_name': self.name,
            'name': self.name,
            'code': self.code,
            'price': "%s" % self.list_price,  # TODO: Format Currency
            'image_urls': [{
                'large': self.image,
                'thumbnail': self.image,
                'regular': self.image,
            }],
        }


class ChannelListing(Model):
    __model_name__ = 'product.product.channel_listing'

    _eager_fields = set(['channel', 'product', 'product.template'])

    product_identifier = StringType()
    state = StringType()

    @classmethod
    def from_slug(cls, slug):
        return cls.query.filter_by_domain(
            [
                ('channel', '=', current_channel.id),
                ('product_identifier', '=', slug),
            ]
        ).first()

    @property
    def channel(self):
        return self._values['channel']

    @property
    def template(self):
        return ProductTemplate.from_cache(self._values['product.template'])

    @property
    def product(self):
        return Product.from_cache(self._values['product'])

    @property
    def unit_price(self):
        # TODO: Price should come from the listing and customer
        return self.product.list_price

    @classmethod
    def get_shop_query(cls):
        return ShopQuery(cls.rpc, cls)

    def get_availability(self):
        return self.rpc.get_availability(self.id)

    def get_absolute_url(self):
        return url_for('products.product', handle=self.product_identifier)


class ProductVariationAttributes(Model):
    __model_name__ = 'product.variation_attributes'

    attribute = ModelType('product.attribute')
    sequence = IntType()
    widget = StringType()
    template = ModelType('product.template')

    def serialize(self):
        """
        Returns serialized version of the attribute::
            {
                'sequence': 1, # Integer id to determine order
                'name': 'shirt color', # Internal name of the attribute
                'display_name': 'Color', # (opt) display name of attr
                'rec_name': 'Color', # The name that should be shown
                'widget': 'swatch', # clue on how to render widget
                'options': [
                    # id, value of the options available to choose from
                    (12, 'Blue'),
                    (13, 'Yellow'),
                    ...
                ]
            }
        """
        if self.attribute.type_ == 'selection':
            # The attribute type needs options to choose from.
            # Send only the options that the products displayed on webshop
            # can have, instead of the exhaustive list of attribute options
            # the attribute may have.
            #
            # For example, the color attribute values could be
            # ['red', 'yellow', 'orange', 'green', 'black', 'blue']
            # but the shirt itself might only be available in
            # ['red', 'yellow']
            #
            # This can be avoided by returning options based on the product
            # rather than on the attributes list of values
            options = set()
            for listing in self.template.listings:
                product = listing.product
                product.refresh()
                value = product.get_attribute_value(self.attribute)
                options.add((value.id, value.name))
        else:
            options = []

        return {
            'sequence': self.sequence,
            'name': self.attribute.name,
            'display_name': self.attribute.display_name,
            'widget': self.widget,
            'options': list(options),
            'attribute_id': self.attribute.id,
        }


class ProductAttribute(Model):
    __model_name__ = 'product.attribute'

    type_ = StringType()
    name = StringType()
    display_name = StringType()


class ProductProductAttribute(Model):
    __model_name__ = 'product.product.attribute'

    attribute = ModelType('product.attribute')
    value_selection = ModelType('product.attribute.selection_option')


class ProductAttributeSelectionOption(Model):
    __model_name__ = 'product.attribute.selection_option'

    name = StringType()


class ProductMedia(Model):
    __model_name__ = 'product.media'

    url = StringType()
