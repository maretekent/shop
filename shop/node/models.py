# -*- coding: utf-8 -*-
"""Node models."""
from shop.fulfilio import Model, StringType


class TreeNode(Model):

    __model_name__ = 'product.tree_node'

    # Set children to be loaded in addition to other fields
    _eager_fields = set(['children', 'image.url'])

    name = StringType()
    slug = StringType()

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
