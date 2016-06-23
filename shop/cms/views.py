# -*- coding: utf-8 -*-
"""CMS views."""
from flask import Blueprint, redirect, url_for

blueprint = Blueprint(
    'pages', __name__,
    url_prefix='/pages', static_folder='../static'
)


@blueprint.route('/')
def pages_root():
    """
    Redirect page root to the home page.
    """
    return redirect(url_for('public.home'))


@blueprint.route('/<handle>')
def page(handle):
    """
    Render a page
    """
    pass


@blueprint.route('/sitemap-index.xml')
def sitemap_index():
    """
    Returns a Sitemap Index Page
    """
    return __doc__


@blueprint.route('/sitemap-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    return __doc__
