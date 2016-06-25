# -*- coding: utf-8 -*-
"""Node models."""
from shop.fulfilio import Model, StringType, IntType


class TreeNode(Model):

    __model_name__ = 'product.tree_node'

    name = StringType()
    item_count = IntType()
    image = StringType()
