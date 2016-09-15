# -*- coding: utf-8 -*-
"""CMS models."""
from flask import url_for
from fulfil_client.model import StringType, One2ManyType

from shop.fulfilio import Model


class MenuItem(Model):

    __model_name__ = 'nereid.cms.menuitem'


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

    def get_absolute_url(self):
        return url_for('pages.category', uri=self.unique_name)


class Article(Model):

    __model_name__ = 'nereid.cms.article'

    uri = StringType()
    title = StringType()
    content = StringType()

    def get_absolute_url(self):
        return url_for('pages.page', uri=self.uri)
