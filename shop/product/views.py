# -*- coding: utf-8 -*-
"""Product views."""
import random

from flask import Blueprint

from shop.node.models import TreeNode
from shop.product.models import Product
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
    img = "https://cdn.shopify.com/s/files/1/0151/2251/products/001_grande.jpg"
    collections = [
        TreeNode(name='Collection 1', item_count=7, image=img),
        TreeNode(name='Very Long Name Collection', item_count=7, image=img),
        TreeNode(name='T-Shirts', item_count=7, image=img),
        TreeNode(name='Colection 4', item_count=7, image=img),
        TreeNode(name='Collection 5', item_count=7, image=img),
        TreeNode(name='Collection 6', item_count=7, image=img),
        TreeNode(name='Collection 7', item_count=7, image=img),
        TreeNode(name='Collection 8', item_count=7, image=img),
    ]
    p_images = [
        "https://cdn.shopify.com/s/files/1/0533/3153/products/1-1_large.jpg?v=1404837242",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/2405/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/682/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/2357/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/2356/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/386/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        "https://dzhj8173mkary.cloudfront.net/static-file-transform/388/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
    ]
    new_arrivals = [
        Product(name='Product 1', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 2', price="$40.00", image=random.choice(p_images)),
        Product(name='Product long one 3', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 4', price="$140.00", image=random.choice(p_images)),
        Product(name='Product 5', price="$10,040.00", image=random.choice(p_images)),
        Product(name='Product 6', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product longer longer 7', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 8', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 9', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 10', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 11', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 12', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 13', price="$1,040.00", image=random.choice(p_images)),
        Product(name='Product 14', price="$1,040.00", image=random.choice(p_images)),
    ]
    return render_template(
        'product/shop.html',
        collections=collections,
        new_arrivals=new_arrivals,
    )


@blueprint.route('/<handle>')
def product(handle):
    """
    Display a specific product with given URI
    """
    return __doc__


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
