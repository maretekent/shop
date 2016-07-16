# -*- coding: utf-8 -*-
"""Node models."""
from shop.fulfilio import IntType, Model, StringType
from shop.product.models import ChannelListing, Product, ProductTemplate


class TreeNode(Model):

    __model_name__ = 'product.tree_node'

    # Set children to be loaded in addition to other fields
    _eager_fields = set(['children', 'image.url', 'products'])

    name = StringType()
    slug = StringType()
    display = StringType()
    description = StringType()
    products_per_page = IntType()

    @property
    def image(self):
        # TODO: A default image?
        return self._values.get('image.url')

    @property
    def item_count(self):
        # TODO: Fix me
        return 10

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

    def _get_items(self):
        """
        Return the items on the node. If the node displays templates, then
        the items are templates. If the node displays products, then the
        items are products.

        This method does a lot of expensive network requests, so the results
        are cached for performance.
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
            listings, key=lambda l: product_ids.index(l['product'])
        )

        # Add the items to
        items = []
        for listing in listings:
            if self.display == 'product.product':
                items.append(listing.id)

    def get_listings(self, page, per_page=None):
        """
        Get the products or templates (hence items) in this node.
        """
        if per_page is None:
            per_page = self.products_per_page



class TreeProductRel(Model):
    __model_name__ = 'product.product-product.tree_node'
