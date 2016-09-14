# -*- coding: utf-8 -*-
"""Node views."""
from flask import Blueprint, abort

from shop.node.models import TreeNode
from shop.utils import render_theme_template as render_template
from shop.utils import dummy_products

blueprint = Blueprint(
    'node', __name__,
    url_prefix='/nodes', static_folder='../static'
)


@blueprint.route('/')
def nodes():
    """
    List All Root Tree Nodes
    """
    nodes = TreeNode.get_root_nodes()
    return render_template('node/nodes.html', nodes=nodes)


# TODO: Cache
def get_products_in_node(node_id, page, per_page):
    """
    Return products in a page for the node
    """
    return []


# TODO: Cache for a day
@dummy_products
def get_top_sellers_in_node(node_id):
    """
    Return the top sellers in the node
    """


@blueprint.route('/<int:id>')
@blueprint.route('/<int:id>/<handle>')                  # Legacy
@blueprint.route('/<int:id>/<handle>/page-<int:page>')  # Legacy
def node(id=None, handle=None, page=1):
    """
    Display a specific node with given URI.

    Shows both the sub nodes and products under it.
    """
    per_page = 10

    if id:
        node = TreeNode.query.get(id)
    else:
        node = TreeNode.query.filter_by_domain([
            ('slug', '=', handle)
        ]).first()

    if not node:
        abort(404)

    listings = node.get_listings(page, per_page)

    top_sellers = []
    if not listings:
        # no direct products under the category.
        # Find top sellers
        top_sellers = get_top_sellers_in_node(node.id)

    return render_template(
        'node/node.html',
        node=node,
        listings=listings,
        top_sellers=top_sellers,
        page=page
    )


@blueprint.route('/sitemap-index.xml')
def sitemap_index():
    """
    Returns a Sitemap Index Page
    """
    return __doc__


@blueprint.route('/sitemaps-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    return __doc__
