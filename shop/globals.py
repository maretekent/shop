from flask.globals import LocalProxy, _find_app, current_app


def _find_cache():
    """
    The application context will be automatically handled by
    _find_app method in flask
    """
    app = _find_app()
    return app.cache


def _get_current_channel():
    from shop.public.models import Channel
    return Channel.get_by_id(current_app.config['FULFIL_CHANNEL'])


def _get_current_cart():
    from shop.cart.models import Cart
    return Cart.get_active()

cache = LocalProxy(_find_cache)
current_channel = LocalProxy(lambda: _get_current_channel())
current_cart = LocalProxy(lambda: _get_current_cart())
