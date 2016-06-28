# -*- coding: utf-8 -*-
"""Node views."""
from flask import Blueprint, abort

from shop.node.models import TreeNode
from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'node', __name__,
    url_prefix='/nodes', static_folder='../static'
)


@blueprint.route('/')
def nodes():
    """
    List All Root Tree Nodes
    """
    nodes = TreeNode.query.filter_by_domain(
        [('parent', '=', None)]
    ).all()
    return render_template('node/nodes.html', nodes=nodes)


@blueprint.route('/<int:id>')
@blueprint.route('/<int:id>/<handle>')                  # Legacy
@blueprint.route('/<int:id>/<handle>/page-<int:page>')  # Legacy
def node(handle=None, id=None):
    """
    Display a specific node with given URI.

    Shows both the sub nodes and products under it.
    """
    if id:
        node = TreeNode.query.get(id)
    else:
        node = TreeNode.query.filter_by_domain([
            ('slug', '=', handle)
        ]).first()
    if not node:
        abort(404)

    return render_template('node/node.html', node=node)


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
