# -*- coding: utf-8 -*-
"""Product models."""
from shop.fulfilio import CurrencyType, Model, StringType
from shop.utils import get_random_product


class ProductTemplate(Model):

    __model_name__ = 'product.template'

    name = StringType()


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
