# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, request

from shop.product.models import ChannelListing, Product
from shop.utils import render_theme_template as render_template
from shop.utils import get_random_product

blueprint = Blueprint(
    'products', __name__,
    url_prefix='/products', static_folder='../static'
)


@blueprint.route('/')
def products():
    """
    List All Root Tree Nodes
    """
    from shop.node.models import TreeNode

    collections = TreeNode.get_root_nodes()
    new_arrivals = [
        get_random_product() for c in range(10)
    ]
    return render_template(
        'product/shop.html',
        collections=collections,
        new_arrivals=new_arrivals,
    )


@blueprint.route('/<handle>')
def product(handle):
    """
    Display a specific product with given URI
    """
    from shop.node.models import TreeNode

    listing = ChannelListing.from_slug(handle)
    if not listing:
        abort(404)

    if 'node' in request.args:
        node = TreeNode.query.get(request.args.get('node', type=int))
    else:
        node = None

    return render_template(
        'product/product.html',
        listing=listing,
        product=listing.product,
        node=node,
    )


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
