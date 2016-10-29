# -*- coding: utf-8 -*-
"""Product models."""
from flask import url_for, current_app
from fulfil_client.model import (MoneyType, IntType, ModelType, One2ManyType,
                                 StringType)
from shop.fulfilio import Model, ShopQuery
from shop.globals import current_channel
from shop.utils import get_random_product, imgixify
from fulfil_client.client import loads, dumps


class ProductTemplate(Model):

    __model_name__ = 'product.template'

    name = StringType()
    media = One2ManyType("product.media", cache=True)
    variation_attributes = One2ManyType(
        "product.variation_attributes", cache=True
    )

    @property
    def lowest_price(self):
        return min([
            listing.unit_price for listing in self.listings
        ])

    @property
    def highest_price(self):
        return max([
            listing.unit_price for listing in self.listings
        ])

    @property
    def listings(self):
        return self._get_listings()

    @property
    def image(self):
        if self.media:
            image = self.media[0].url
            return imgixify([image])[0]
        else:
            # Iterate through listings to find an image
            for listing in self.listings:
                image = listing.product.image
                if image:
                    return image

    def _get_listings(self):
        """
        Return the products (that are listed in the current channel) and
        active.
        """
        key = "%s:%s:listing_ids" % (self.__model_name__, self.id)
        if self.cache_backend.exists(key):
            listing_ids = loads(self.cache_backend.get(key))
            return ChannelListing.from_cache(listing_ids)
        else:
            listings = ChannelListing.query.filter_by_domain(
                [
                    ('channel', '=', current_channel.id),
                    ('state', '=', 'active'),
                    ('product.template', '=', self.id),
                ],
            ).all()
            map(lambda l: l.store_in_cache(), listings)
            self.cache_backend.set(
                key, dumps([l.id for l in listings]),
                ex=current_app.config['REDIS_EX']
            )
            return listings

    def get_product_variation_data(self):
        """
        """
        key = '%s:get_product_variation_data:%s' % (
            self.__model_name__, self.id
        )
        if self.cache_backend.exists(key):
            return loads(self.cache_backend.get(key))

        self.refresh()
        variation_attributes = map(
            lambda variation: variation.serialize(),
            self.variation_attributes
        )
        variants = []
        for listing in self.listings:
            product = listing.product
            product.refresh()  # Fetch record again

            data = product.serialize(purpose='variant_selection')
            data['inventory_status'] = listing.get_availability()['value']
            data['attributes'] = {}

            for variation in self.variation_attributes:
                attribute = variation.attribute     # actual attribute
                value = product.get_attribute_value(attribute)
                data['attributes'][attribute.id] = value

            variants.append(data)

        rv = {
            'variants': variants,
            'variation_attributes': variation_attributes,
        }
        self.cache_backend.set(
            key, dumps(rv),
            ex=current_app.config['REDIS_EX'],
        )
        return rv


class Product(Model):

    __model_name__ = 'product.product'

    _eager_fields = set([
        'template', 'variant_name', 'default_image.url'
    ])

    code = StringType()
    list_price = MoneyType('currency_code')
    description = StringType()
    long_description = StringType()
    uri = StringType()
    attributes = One2ManyType("product.product.attribute", cache=True)
    cross_sells = One2ManyType('product.product', cache=True)

    @property
    def currency_code(self):
        return current_channel.currency_code

    @property
    def image(self):
        image = self._values.get('default_image.url')
        if image:
            return imgixify([image])[0]
        return image

    @property
    def images(self):
        key = '%s:images:%s' % (self.__model_name__, self.id)
        if self.cache_backend.exists(key):
            return loads(self.cache_backend.get(key))
        else:
            rv = self.rpc.get_images_urls(self.id)
            rv = imgixify(rv)
            self.cache_backend.set(
                key, dumps(rv),
                ex=current_app.config['REDIS_EX'],
            )
            return rv

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
                value = getattr(
                    product_attr,
                    'value_%s' % attribute.type_
                )
                if value and attribute.type_ == 'selection':
                    value = value.id
                return value
        else:
            if silent:
                return
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
        key = '%s:from_slug:%s:%s' % (
            cls.__model_name__, slug, current_channel.id
        )
        if cls.cache_backend.exists(key):
            return cls.from_cache(loads(cls.cache_backend.get(key)))
        else:
            listing = cls.query.filter_by_domain(
                [
                    ('channel', '=', current_channel.id),
                    ('product_identifier', '=', slug),
                ]
            ).first()
            if listing:
                cls.cache_backend.set(
                    key, listing.id,
                    ex=current_app.config['REDIS_EX']
                )
                listing.store_in_cache()
            return listing

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

    def get_absolute_url(self, node=None):
        kwargs = {
            'handle': self.product_identifier
        }
        if node is not None:
            kwargs['node'] = node
        return url_for('products.product', **kwargs)


class ProductVariationAttributes(Model):
    __model_name__ = 'product.variation_attributes'

    attribute = ModelType('product.attribute', cache=True)
    sequence = IntType()
    widget = StringType()
    template = ModelType('product.template', cache=True)

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
                if value:
                    option = ProductAttributeSelectionOption.from_cache(value)
                    options.add((option.id, option.name))
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

    attribute = ModelType('product.attribute', cache=True)
    value_selection = ModelType(
        'product.attribute.selection_option', cache=True
    )


class ProductAttributeSelectionOption(Model):
    __model_name__ = 'product.attribute.selection_option'

    name = StringType()


class ProductUOM(Model):
    __model_name__ = 'product.uom'

    symbol = StringType()


class ProductMedia(Model):
    __model_name__ = 'product.media'

    url = StringType()
