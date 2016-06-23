# -*- coding: utf-8 -*-
"""Node views."""
from flask import Blueprint

blueprint = Blueprint(
    'node', __name__,
    url_prefix='/nodes', static_folder='../static'
)


@blueprint.route('/')
def nodes():
    """
    List All Root Tree Nodes
    """
    # TODO
    return __doc__


@blueprint.route('/<int:id>/<handle>')                  # Legacy
@blueprint.route('/<int:id>/<handle>/page-<int:page>')  # Legacy
def node(handle=None, id=None):
    """
    Display a specific node with given URI.

    Shows both the sub nodes and products under it.
    """
    # TODO
    return __doc__


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
