# -*- coding: utf-8 -*-
"""CMS models."""
from shop.fulfilio import Model
from fulfil_client.model import StringType


class MenuItem(Model):

    __model_name__ = 'nereid.cms.menuitem'


class BannerCategory(Model):

    __model_name__ = 'nereid.cms.banner.category'


class Banner(Model):

    __model_name__ = 'nereid.cms.banner'


class ArticleCategory(Model):

    __model_name__ = 'nereid.cms.article.category'


class Article(Model):

    __model_name__ = 'nereid.cms.article'

    uri = StringType()
    title = StringType()
    content = StringType()
