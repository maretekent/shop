# -*- coding: utf-8 -*-
"""Product views."""
import random

from flask import Blueprint, abort, request

from shop.node.models import TreeNode
from shop.product.models import Product
from shop.utils import render_theme_template as render_template, get_random_product

blueprint = Blueprint(
    'products', __name__,
    url_prefix='/products', static_folder='../static'
)


@blueprint.route('/')
def products():
    """
    List All Root Tree Nodes
    """
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
@blueprint.route('/<int:id>')
def product(handle=None, id=None):
    """
    Display a specific product with given URI
    """
    if id:
        product = Product.query.get_or_404(id)
    elif handle:
        product = Product.query.filter_by_domain([
            ('uri', 'ilike', handle),
        ]).first()
    else:
        abort(404)

    print product._values

    if 'node' in request.args:
        node = TreeNode.query.get(request.args.get('node', type=int))
    else:
        node = None

    return render_template(
        'product/product.html',
        product=product,
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
