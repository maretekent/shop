# -*- coding: utf-8 -*-
"""Public models."""

from flask import current_app
from fulfil_client import model
from shop.fulfilio import Model
from fulfil_client.client import loads, dumps


class Channel(Model):
    __model_name__ = 'sale.channel'

    _eager_fields = set(['anonymous_customer', 'currency.code'])

    name = model.StringType()
    code = model.StringType()
    anonymous_customer = model.ModelType('party.party')

    # TODO: convert followings to model type.
    company = model.IntType()
    currency = model.IntType()
    warehouse = model.IntType()
    # support_email = StringType()
    payment_gateway = model.ModelType('payment_gateway.gateway', cache=True)

    @property
    def currency_code(self):
        return self._values.get('currency.code')

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
        key = '%s:get_list' % (cls.__model_name__,)
        if cls.cache_backend.exists(key):
            countries = cls.from_cache(
                loads(cls.cache_backend.get(key))
            )
        else:
            enabled = current_app.config.get('ENABLED_COUNTRIES', [])
            if enabled:
                countries = cls.query.filter_by_domain([
                    ('code', 'in', enabled)
                ]).all()
            else:
                countries = cls.query.all()
            map(lambda s: s.store_in_cache(), countries)
            cls.cache_backend.set(
                key, dumps([c.id for c in countries]),
                ex=current_app.config['REDIS_EX'],
            )
        return countries

    def store_in_cache(self):
        """
        Store the code in the cache for easy cache
        based retreival.
        """
        super(Country, self).store_in_cache()
        key = '%s:from_code:%s' % (self.__model_name__, self.code)
        self.cache_backend.set(
            key, self.id,
            ex=current_app.config['REDIS_EX'],
        )

    @classmethod
    def from_code(cls, code):
        code = code.upper()
        key = '%s:from_code:%s' % (cls.__model_name__, code)
        if cls.cache_backend.exists(key):
            return cls.from_cache(int(cls.cache_backend.get(key)))
        else:
            country = cls.query.filter_by_domain([
                ('code', 'ilike', code)
            ]).first()
            if country:
                country.store_in_cache()
            return country

    @property
    def subdivisions(self):
        key = '%s:subdivisions:%s' % (self.__model_name__, self.id)
        if self.cache_backend.exists(key):
            subdivisions = Subdivision.from_cache(
                loads(self.cache_backend.get(key))
            )
        else:
            subdivisions = Subdivision.query.filter_by(country=self.id).all()
            map(lambda s: s.store_in_cache(), subdivisions)
            self.cache_backend.set(
                key, dumps([s.id for s in subdivisions]),
                ex=current_app.config['REDIS_EX'],
            )
        return subdivisions

    def get_subdivision(self, code):
        """
        Get a subdivision given the code
        """
        code = code.upper()
        for subdivision in self.subdivisions:
            if subdivision.code.upper() == code:
                return subdivision


class Subdivision(Model):

    __model_name__ = 'country.subdivision'
    _eager_fields = set(['code'])

    name = model.StringType()
    country = model.ModelType("country.country", cache=True)

    @property
    def code(self):
        if self._values.get('code'):
            return self._values['code'].split('-')[-1]


class StaticFile(Model):

    __model_name__ = 'nereid.static.file'

    name = model.StringType()
    url = model.StringType()


class Banner(Model):

    __model_name__ = 'nereid.cms.banner'

    name = model.StringType()
    file = model.ModelType('nereid.static.file', cache=True)
    sequence = model.IntType()
    description = model.StringType()
    click_url = model.StringType()
