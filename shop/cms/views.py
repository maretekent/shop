# -*- coding: utf-8 -*-
"""CMS views."""
from flask import Blueprint, abort, make_response, redirect, url_for

from shop.cms.models import Article, ArticleCategory
from shop.utils import render_theme_template as render_template

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


@blueprint.route('/<uri>')
def page(uri):
    """
    Render a page
    """
    article = Article.query.filter_by(uri=uri).first()
    if article:
        return render_template('cms/page.html', article=article)
    return abort(404)


@blueprint.route('/category/<uri>')
def category(uri):
    """
    Render a category
    """
    category = ArticleCategory.query.filter_by(unique_name=uri).first()
    return render_template('cms/category.html', category=category)


@blueprint.route('/sitemap-index.xml')
def render_xml_sitemap():
    """
    Returns a Sitemap Index Page
    """
    articles =  Article.query.filter_by_domain(
        [('state', '=', 'published')]
    ).all()
    nodes = []
    for article in articles:
        nodes.append(
            {
                'url_data': article.get_absolute_url(_external=True),
                'lastmod': article.published_on
            }
        )

    sitemap_xml = render_template('cms/sitemap.xml', nodes=nodes)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response


@blueprint.route('/sitemap-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    return __doc__
