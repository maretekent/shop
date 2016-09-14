# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, request

from shop.globals import current_channel
from shop.product.models import ChannelListing
from shop.utils import render_theme_template as render_template

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
    page = request.args.get('page', type=int) or None
    per_page = request.args.get('per_page', type=int) or 24  # default to suit the view
    shop_query = ChannelListing.get_shop_query().filter_by_domain([
        ('channel', '=', current_channel.id),
    ])
    paginate = shop_query.paginate(page=page, per_page=per_page)
    return render_template(
        'product/shop.html',
        collections=collections,
        new_arrivals=paginate.items,
        paginate=paginate,
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
