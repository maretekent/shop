# -*- coding: utf-8 -*-
"""Product models."""
from shop.fulfilio import Model, StringType, CurrencyType


class ProductTemplate(Model):

    __model_name__ = 'product.template'


class Product(Model):

    __model_name__ = 'product.product'

    name = StringType()
    price = CurrencyType()
    image = StringType()
