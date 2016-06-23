# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint

blueprint = Blueprint(
    'products', __name__,
    url_prefix='/products', static_folder='../static'
)


@blueprint.route('/')
def products():
    """
    List All Root Tree Nodes
    """
    # TODO
    return __doc__


@blueprint.route('/<handle>')
def product(handle):
    """
    Display a specific product with given URI
    """
    # TODO
    return __doc__


@blueprint.route('/sitemaps/product-index.xml')
def sitemap_index():
    """
    Returns a Sitemap Index Page
    """
    return __doc__


@blueprint.route('/sitemaps/product-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    return __doc__
