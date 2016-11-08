# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, make_response, request, jsonify, url_for
from shop.globals import current_channel
from shop.product.models import ChannelListing, ProductTemplate
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
        node = TreeNode.from_cache(request.args.get('node', type=int))
    else:
        node = None

    return render_template(
        'product/product.html',
        listing=listing,
        product=listing.product,
        node=node,
    )


@blueprint.route('/get-variations')
def get_variations():
    template_id = request.args.get('template', type=int)
    template = ProductTemplate.from_cache(template_id)
    return jsonify(template.get_product_variation_data())


@blueprint.route('/sitemaps/sitemap-index.xml')
def sitemap_index():
    shop_query = ChannelListing.get_shop_query().filter_by_domain([
        ('channel', '=', current_channel.id),
    ])
    paginate = shop_query.paginate(per_page=100)
    sitemaps = []
    for x in xrange(1, paginate.pages + 1):
        sitemaps.append(
            {
                'loc': url_for(
                    'products.sitemap',
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

@blueprint.route('/sitemaps/sitemap-<int:page>.xml')
def sitemap(page=1):
    """
    Returns a Sitemap Index Page
    """
    shop_query = ChannelListing.get_shop_query().filter_by_domain([
        ('channel', '=', current_channel.id),
    ])
    # Default per_page 100, a max size of 10Mb is advised otherwise
    paginate = shop_query.paginate(page=page, per_page=100)
    urls = []
    for product in paginate.items:
        urls.append(
            {
                'loc': product.get_absolute_url(_external=True)
            }
        )
    sitemap_xml = render_template('partials/sitemap.xml', urls=urls)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response
