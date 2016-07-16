from flask.globals import (
    _request_ctx_stack, current_app,
    request, session, g, LocalProxy, _find_app
)
from fulfilio import Channel

def _find_cache():
    """
    The application context will be automatically handled by
    _find_app method in flask
    """
    app = _find_app()
    return app.cache

def _get_current_channel():
    return Channel.get_by_id(current_app.config['FULFIL_CHANNEL'])

cache = LocalProxy(_find_cache)
current_channel = LocalProxy(lambda: _get_current_channel())