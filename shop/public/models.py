# -*- coding: utf-8 -*-
"""Public models."""

from fulfil_client import model

from shop.fulfilio import Model


class Channel(Model):
    __model_name__ = 'sale.channel'

    _eager_fields = {'anonymous_customer'}

    name = model.StringType()
    code = model.StringType()
    anonymous_customer = model.ModelType('party.party')

    # TODO: convert followings to model type.
    company = model.IntType()
    currency = model.IntType()
    warehouse = model.IntType()
    # support_email = StringType()

    @property
    def support_email(self):
        # TODO: Add support email to channel
        # This is a temporary hack until then
        import os
        return os.environ['FROM_EMAIL']


class Country(Model):

    __model_name__ = 'country.country'

    name = model.StringType()
    code = model.StringType()

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

    name = model.StringType()
    country = model.ModelType("country.country")


class StaticFile(Model):

    __model_name__ = 'nereid.static.file'

    name = model.StringType()
    url = model.StringType()


class Banner(Model):

    __model_name__ = 'nereid.cms.banner'

    name = model.StringType()
    file = model.ModelType('nereid.static.file')
    sequence = model.IntType()
    description = model.StringType()
