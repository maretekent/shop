# -*- coding: utf-8 -*-
"""CMS models."""
from fulfil_client.model import StringType

from shop.fulfilio import Model


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
