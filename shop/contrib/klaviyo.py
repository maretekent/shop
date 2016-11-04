# -*- coding: utf-8 -*-
"""
Optional extension to use Klaviyo with shop.

This module provides a function that can be used as a Jinja filter
on your templates to push information to klavio.

* Step 1: Add the klavio snippet with the API key to your base layout template
* Step 2: Add to product, delivery, checkout pages.
  More instructions can be found at: http://docs.klaviyo.com/customer/en/portal/articles/2476708-integrate-a-custom-ecommerce-cart-or-platform#section0     #noqa
* Step 3: Use the filter to render JS that pushes to klaviyo

For layout page
===============

Add before </body>

```
<script>
  var _learnq = _learnq || [];
  _learnq.push(['account', 'YOUR_PUBLIC_API_KEY']);
  (function () {
    var b = document.createElement('script'); b.type = 'text/javascript'; b.async = true;
    b.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'a.klaviyo.com/media/js/analytics/analytics.js';
    var a = document.getElementsByTagName('script')[0]; a.parentNode.insertBefore(b, a);
  })();
  {% if not current_user.is_anonymous %}
  _learnq.push(['identify', {{ current_user|klaviyo|tojson|safe }}]);
  {% endif %}
</script>
{% block klaviyo %}{% endblock klaviyo %}
```


For product pages
=================

```
{% block klaviyo %}
<script>
  var _learnq = _learnq || [];
  _learnq.push(['track', 'Viewed Product', {{ listing|klaviyo|tojson|safe }}]);
</script>
{% endblock klaviyo %}
```

For the first checkout step
===========================

```
{% block klaviyo %}
<script>
_learnq.push(['track', 'Started Checkout', {{ current_cart.sale|klaviyo|tojson|safe }}]);
</script>
{% endblock %}
```

For order-confirmation page
===========================

```
{% block klaviyo %}
<script>
_learnq.push(['track', 'Placed Order', {{ sale|klaviyo|tojson|safe }}]);
{% for line in sale.lines %}
_learnq.push(['track', 'Ordered Product', {{ line|klaviyo|tojson|safe }}]);
{% endfor %}
```

Checking if this is working
===========================

Activity feeds on the klaviyo site is the best place to check if your pages
are reporting information.

Read more: http://docs.klaviyo.com/customer/en/portal/articles/2476708-integrate-a-custom-ecommerce-cart-or-platform#section5   #noqa

"""
from shop.cart.models import Sale, SaleLine
from shop.product.models import ChannelListing
from shop.user.models import User


def klaviyo_filter(record):
    if isinstance(record, User):
        return user_to_dict(record)
    elif isinstance(record, ChannelListing):
        return listing_to_dict(record)
    elif isinstance(record, Sale):
        return sale_to_dict(record)
    elif isinstance(record, SaleLine):
        return sale_line_to_dict(record)


def user_to_dict(user):
    return {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'Fulfil Contact': user.party.__client_url__,
        'Fulfil Web User': user.__client_url__,
    }


def listing_to_dict(listing):
    """
    Return a JSON serializable dictionary representing the product with
    Klaviyo's key value pairs.
    """
    product = listing.product
    return {
        'Title': product.name,
        'ItemId': product.id,
        'Categories': [node.name for node in product.nodes],
        'ImageUrl': product.image,
        'Url': listing.get_absolute_url(_external=True),
        'Metadata': {
            'Price': listing.unit_price.amount,
            'CompareAtPrice': product.list_price.amount,
        }
    }


def sale_to_dict(sale):
    return {
        '$event_id': sale.id,
        '$value': sale.total_amount.amount,
        'Items': [
            sale_line_to_dict(line)
            for line in sale.lines
        ],
        'ItemNames': [line.product.name for line in sale.lines]
    }


def sale_line_to_dict(line):
    product = line.product
    return {
        'SKU': product.code,
        'Name': product.name,
        'Quantity': line.quantity,
        'ItemPrice': line.unit_price.amount,
        'RowTotal': line.amount.amount,
        'ProductURL': product.listing.get_absolute_url(_external=True),
        'ImageURL': product.image,
        # 'ProductCategories' : ["Fiction", "Children"]
    }
