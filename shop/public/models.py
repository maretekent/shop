# -*- coding: utf-8 -*-
"""Public models."""

from fulfil_client.model import ModelType, StringType
from shop.fulfilio import Model


class Country(Model):

    __model_name__ = 'country.country'

    name = StringType()
    code = StringType()

    @classmethod
    def get_list(cls):
        # TODO: Implement a cache
        return cls.query.all()

    @property
    def subdivisions(self):
        # TODO: Implement a cache
        return Subdivision.query.filter_by(country=self.id).all()


class Subdivision(Model):

    __model_name__ = 'country.subdivision'

    name = StringType()
    country = ModelType(model=Country)
