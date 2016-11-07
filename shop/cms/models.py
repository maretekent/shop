# -*- coding: utf-8 -*-
"""CMS models."""
from flask import url_for, current_app
from fulfil_client.model import One2ManyType, StringType
from shop.fulfilio import Model, ShopQuery
from fulfil_client.client import loads, dumps


class MenuItem(Model):

    __model_name__ = 'nereid.cms.menuitem'

    title = StringType()
    target = StringType()
    type_ = StringType()

    def get_tree(self, depth):
        key = '%s:get_tree:%s:%s' % (self.__model_name__, self.id, depth)
        if self.cache_backend.exists(key):
            return loads(self.cache_backend.get(key))
        else:
            rv = self.rpc.get_menu_item(self.id, depth)
            self.cache_backend.set(
                key, dumps(rv), current_app.config['REDIS_EX']
            )
            return rv

    @classmethod
    def get_nav(cls, code):
        key = '%s:get_nav:%s' % (cls.__model_name__, code)
        if cls.cache_backend.exists(key):
            menu_item = cls.from_cache(loads(cls.cache_backend.get(key)))
        else:
            menu_item = cls.query.filter_by(code=code).first()
            cls.cache_backend.set(
                key, dumps(menu_item.id), current_app.config['REDIS_EX']
            )
            menu_item.store_in_cache()
        return menu_item


class BannerCategory(Model):

    __model_name__ = 'nereid.cms.banner.category'


class Banner(Model):

    __model_name__ = 'nereid.cms.banner'


class ArticleCategory(Model):

    __model_name__ = 'nereid.cms.article.category'

    title = StringType()
    unique_name = StringType()
    description = StringType()
    published_articles = One2ManyType('nereid.cms.article')

    def get_absolute_url(self, **kwargs):
        return url_for('pages.category', uri=self.unique_name, **kwargs)


class Article(Model):

    __model_name__ = 'nereid.cms.article'

    uri = StringType()
    title = StringType()
    content = StringType()
    published_on = StringType()

    @classmethod
    def get_shop_query(cls):
        return ShopQuery(cls.rpc, cls)

    def get_absolute_url(self, **kwargs):
        return url_for('pages.page', uri=self.uri, **kwargs)
