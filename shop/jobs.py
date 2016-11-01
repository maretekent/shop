# -*- coding: utf-8 -*-
from shop.extensions import celery


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


@celery.task()
def cache_nodes():
    from shop.node.models import TreeNode
    nodes = TreeNode.query.all()
    for node in nodes:
        node.store_in_cache()
        cache_node.delay(node.id)


@celery.task()
def cache_products():
    from shop.product.models import Product
    products = Product.query.all()
    for product in products:
        product.store_in_cache()


@celery.task()
def cache_templates():
    from shop.product.models import ProductTemplate
    templates = ProductTemplate.query.all()
    for template in templates:
        template.store_in_cache()
        cache_template.delay(template.id)


@celery.task()
def cache_listings():
    from shop.product.models import ChannelListing
    listings = ChannelListing.query.all()
    for listing in listings:
        listing.store_in_cache()


@celery.task()
def cache_template(template_id):
    from shop.product.models import ProductTemplate
    template = ProductTemplate.from_cache(template_id)
    template._get_listings()
    template.get_product_variation_data()


@celery.task()
def cache_node(node_id):
    from shop.node.models import TreeNode
    node = TreeNode.from_cache(node_id)
    node._cache_items()
