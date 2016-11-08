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
def sitemap_index():
    """
    Returns a Sitemap Index Page of articles
    """
    shop_query = Article.get_shop_query().filter_by_domain([
        ('state', '=', 'published'),
    ])
    paginate = shop_query.paginate(per_page=100)
    sitemaps = []
    for x in xrange(1, paginate.pages + 1):
        sitemaps.append(
            {
                'loc': url_for(
                    'pages.sitemap',
                    page=x,
                    _external=True
                )
            }
        )
    sitemap_xml = render_template(
        'partials/sitemap-index.xml',
        sitemaps=sitemaps
    )
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response


@blueprint.route('/sitemap-<int:page>.xml')
def sitemap(page):
    """
    Returns a specific page of the sitemap
    """
    shop_query = Article.get_shop_query().filter_by_domain([
        ('state', '=', 'published'),
    ])
    # Default per_page 100, a max size of 10Mb is advised otherwise
    paginate = shop_query.paginate(page=page, per_page=100)
    urls = []
    for article in paginate.items:
        urls.append(
            {
                'loc': article.get_absolute_url(_external=True),
                'lastmod': article.published_on
            }
        )

    sitemap_xml = render_template('partials/sitemap.xml', urls=urls)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response
