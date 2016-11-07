# -*- coding: utf-8 -*-
"""
Optional extension to use Google Analytics Enhanced eCommerce on your store.

This is designed to be used with tag manager and it's dataLayer implementation.
Read: https://developers.google.com/tag-manager/enhanced-ecommerce
"""
import simplejson as json
from shop.cart.models import Sale, SaleLine
from shop.product.models import ChannelListing


class GADataLayerScript(dict):
    def __html__(self):
        return """
            <script>
                if ("dataLayer" in window) {dataLayer.push(%s);}
            </script>
        """ % json.dumps(self)


def ga_filter(record, *args, **kwargs):
    if isinstance(record, ChannelListing):
        return listing_to_dict(record, *args, **kwargs)
    elif isinstance(record, Sale):
        return sale_to_dict(record, *args, **kwargs)
    elif isinstance(record, SaleLine):
        return sale_line_to_dict(record, *args, **kwargs)


def ga_impression(listings, list=None, currency='USD'):
    """
    Measure product impressions by using the impression action
    """
    res = {
        'ecommerce': {
            'currencyCode': currency,
            'impressions': []
        }
    }
    for position, listing in enumerate(listings, start=1):
        res['recommerce']['impressions'].append(
            listing_to_dict(listing, position, list)
        )
    return GADataLayerScript(res)


def ga_detail(product, list=None, currency='USD'):
    res = {
        'ecommerce': {
            'currencyCode': currency,
            'detail': {
                'products': [
                    product_to_dict(product, list=list)
                ]
            }
        }
    }
    if list:
        res['ecommerce']['detail']['actionField'] = {
            'list': list,
        }
    return GADataLayerScript(res)


def ga_checkout(sale, step, option=None):
    res = {
        'event': 'checkout',
        'ecommerce': {
            'checkout': {
                'actionField': {'step': step, 'option': option},
                'products': []
            }
        }
    }
    for line in sale.lines:
        res['ecommerce']['checkout']['products'].append(
            sale_line_to_dict(line)
        )
    return GADataLayerScript(res)


def ga_purchase(sale):
    res = {
        'ecommerce': {
            'purchase': {
                'actionField': sale_to_dict(sale),
                'products': filter(None, [
                    sale_line_to_dict(line)
                    for line in sale.lines
                ])
            }
        }
    }
    return GADataLayerScript(res)


def listing_to_dict(listing, position=None, list=None):
    """
    Return a JSON serializable dictionary representing the product with
    GA key value pairs
    """
    if not (listing and listing.product):
        return {}
    return product_to_dict(listing.product, position, list)


def product_to_dict(product, position=None, list=None):
    res = {
        'id': product.code,
        'name': product.template.name,
        'variant': product.name,
        'price': product.list_price.amount,
        'brand': product.brand,
    }
    if product.nodes:
        res['category'] = product.nodes[0].name
    if position:
        res['position'] = position
    if list:
        res['list'] = list
    return res


def sale_to_dict(sale):
    res = {
        'id': sale.number or sale.id,
        'revenue': sale.total_amount.amount,
        'tax': sale.tax_amount.amount,
        'shipping': sale.total_shipment_cost.amount,
        'coupon': sale.promo_code,
    }
    return res


def sale_line_to_dict(line):
    if not line.product.listing:
        return {}
    res = product_to_dict(line.product)
    res['price'] = '{0:0.2f}'.format(line.unit_price.amount)
    res['quantity'] = line.quantity
    return res
