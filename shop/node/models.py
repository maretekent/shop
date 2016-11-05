# -*- coding: utf-8 -*-
"""Node models."""
import sys
from flask import url_for, current_app
from fulfil_client.model import IntType, StringType
from shop.extensions import redis_store
from shop.fulfilio import Model
from shop.product.models import ChannelListing, ProductTemplate
from shop.utils import json_ld_dict
from fulfil_client.client import loads, dumps


class TreeNode(Model):

    __model_name__ = 'product.tree_node'

    # Set children to be loaded in addition to other fields
    _eager_fields = set(['children', 'image.url', 'products'])

    name = StringType()
    slug = StringType()
    display = StringType()
    description = StringType()
    products_per_page = IntType()

    left = IntType()
    right = IntType()

    @property
    def image(self):
        # TODO: A default image?
        return self._values.get('image.url')

    @property
    def item_count(self):
        # TODO: Fix me
        return 10

    @property
    def templates_count(self):
        return redis_store.zcount(
            self.templates_key, 0, sys.maxint
        )

    @property
    def listings_count(self):
        return redis_store.zcount(
            self.listings_key, 0, sys.maxint
        )

    @property
    def has_children(self):
        return len(self._values['children']) > 0

    @property
    def children(self):
        """
        Return active resources for the child nodes
        """
        return type(self).from_ids(self._values['children'])

    @classmethod
    def get_root_nodes(cls):
        """
        Get the root nodes (without parents)
        """
        return cls.query.filter_by_domain(
            [('parent', '=', None)]
        ).all()

    def _cache_items(self):
        """
        A special method to cache and save listings and templates
        """
        node_products = TreeProductRel.rpc.search_read(
            [
                ('node.left', '>=', self.left),
                ('node.right', '<=', self.right),
                ('product.active', '=', True),
            ],
            None, None, [('sequence', 'ASC')],
            ['id', 'sequence', 'product']
        )

        # Now fetch the listings of the products for the current channel
        product_ids = [n_p['product'] for n_p in node_products]
        listings = ChannelListing.rpc.search_read(
            [
                ('product', 'in', product_ids),
                ('state', '=', 'active'),
            ],
            None, None, None,
            ['id', 'product', 'product.template']
        )

        # Sort the listings in the order of products position in node
        listings = sorted(
            listings,
            key=lambda l: product_ids.index(l['product']),
        )
        # Add the listings to the sorted set in redis
        for position, listing in enumerate(listings):
            redis_store.zadd(
                self.listings_key, position, listing['id'],
            )

        # Now store templates
        templates = []      # A list to avoid duplicates
        for listing in listings:
            if listing['product.template'] in templates:
                continue
            templates.append(listing['product.template'])
        for position, template in enumerate(templates):
            redis_store.zadd(
                self.templates_key, position, template,
            )

        # Set the cache
        redis_store.expire(self.listings_key, current_app.config['REDIS_EX'])
        redis_store.expire(self.templates_key, current_app.config['REDIS_EX'])

    @property
    def listings_key(self):
        return '%s:%s:listings' % (self.__model_name__, self.id)

    @property
    def templates_key(self):
        return '%s:%s:templates' % (self.__model_name__, self.id)

    def get_listings(self, page, per_page=None):
        """
        Get the products or templates (hence items) in this node.
        """
        return map(
            lambda l: ChannelListing.from_cache(int(l)),
            self._get_items(self.listings_key, page, per_page)
        )

    def get_templates(self, page, per_page=None):
        """
        Get the products or templates (hence items) in this node.
        """
        return map(
            lambda t: ProductTemplate.from_cache(int(t)),
            self._get_items(self.templates_key, page, per_page)
        )

    def _get_items(self, key, page, per_page):
        """
        Return paginated items from the sorted set
        referred by the key. It could be templates or listings, this
        method does not care.
        """
        if not redis_store.exists(key):
            self._cache_items()

        if per_page is None:
            per_page = self.products_per_page

        start = (page - 1) * per_page
        end = start + per_page - 1

        return redis_store.zrange(key, start, end)

    def get_absolute_url(self, **kwargs):
        return url_for('node.node', id=self.id, handle=self.slug, **kwargs)

    @classmethod
    def make_tree_crumbs(cls, node_id):
        key = '%s:make_tree_crumbs:%s' % (cls.__model_name__, node_id)
        if cls.cache_backend.exists(key):
            return loads(cls.cache_backend.get(key))
        else:
            rv = cls.rpc.make_shop_tree_crumbs(node_id)
            cls.cache_backend.set(key, dumps(rv))
            return rv

    @property
    def tree_crumbs_json_ld(self):
        items = []
        for position, data_title_pair in enumerate(
                self.make_tree_crumbs(self.id), start=1):
            data, title = data_title_pair
            node = TreeNode(values=data)
            items.append({
                '@type': 'ListItem',
                'position': position,
                'item': {
                    '@id': node.get_absolute_url(_external=True),
                    'name': title,
                    'image': node.image,
                }
            })
        return json_ld_dict({
            '@context': 'http://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': items,
        })

    @classmethod
    def from_slug(cls, slug):
        """
        Return the Node which matches the slug.

        Results are cached for performance
        """
        slug = slug.lower()

        key = '%s:%s' % (cls.__model_name__, slug)

        if cls.cache_backend:
            if not cls.cache_backend.exists(key):
                # Use RPC search for efficient id search
                # (instead of query api)
                ids = cls.rpc.search([('slug', 'ilike', slug)])
                if ids:
                    cls.cache_backend.set(key, ids[0])
                else:
                    raise Exception("Node with slug %s not found" % slug)
            else:
                ids = [int(cls.cache_backend.get(key))]
        return cls.from_cache(ids[0])


class TreeProductRel(Model):
    __model_name__ = 'product.product-product.tree_node'
