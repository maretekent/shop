# -*- coding: utf-8 -*-
"""Node views."""
from flask import Blueprint, abort, make_response
from shop.node.models import TreeNode
from shop.utils import render_theme_template as render_template
from shop.utils import dummy_products, Pagination

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

    if node.display == 'product.template':
        templates = node.get_templates(page, per_page)
        pagination = Pagination(page, per_page, node.templates_count)
        listings = []
    else:
        listings = node.get_listings(page, per_page)
        pagination = Pagination(page, per_page, node.listings_count)
        templates = []

    top_sellers = []
    if not listings:
        # no direct products under the category.
        # Find top sellers
        top_sellers = get_top_sellers_in_node(node.id)

    return render_template(
        'node/node.html',
        node=node,
        listings=listings,
        templates=templates,
        top_sellers=top_sellers,
        pagination=pagination,
        page=page
    )


@blueprint.route('/sitemap-index.xml')
def render_xml_sitemap():
    """
    Renders xml sitemap
    """
    # till depth of 10
    nodes = TreeNode.rpc.get_sitemap_nodes(9)

    sitemap_xml = render_template('node/sitemap.xml', nodes=nodes)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response


@blueprint.route('/sitemaps-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    return __doc__
