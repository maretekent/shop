from shop.cms.models import Article, ArticleCategory
from shop.node.models import TreeNode
from six import string_types


def get_menuitem_link(data):
    """
    Return link to render menu item.
    """
    if isinstance(data, string_types):
        # data is already a link
        return data

    model = None

    if (data['model'] == 'product.tree_node'):
        model = TreeNode(values=data)
    if (data['model'] == 'nereid.cms.article'):
        model = Article(values=data)
    if (data['model'] == 'nereid.cms.article.category'):
        model = ArticleCategory(values=data)

    if model:
        return model.get_absolute_url()
    return "#"
