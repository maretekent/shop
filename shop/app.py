# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask
from shop.assets import assets
from shop.extensions import (babel, cache, csrf_protect, debug_toolbar, fulfil,
                             login_manager, redis_store, sentry, session,
                             themes)
from shop.globals import current_app, current_channel
from shop.settings import ProdConfig
from shop.utils import render_theme_template as render_template


def create_app(config_object=ProdConfig):
    """
    An application factory, as explained here:

    http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # explicitly assign a few config vars that are needed
    app.channel = int(app.config['FULFIL_CHANNEL'])

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_context_processors(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    assets.init_app(app)
    cache.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    fulfil.init_app(app)
    sentry.init_app(app)
    babel.init_app(app)
    redis_store.init_app(app)
    themes.init_themes(app, app_identifier='fulfil-shop')

    # Set the session redis needed for Flask Session
    app.config['SESSION_REDIS'] = redis_store._redis_client
    session.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    import shop.user.views
    app.register_blueprint(shop.user.views.blueprint)
    import shop.public.views
    app.register_blueprint(shop.public.views.blueprint)
    import shop.product.views
    app.register_blueprint(shop.product.views.blueprint)
    import shop.node.views
    app.register_blueprint(shop.node.views.blueprint)
    import shop.cart.views
    app.register_blueprint(shop.cart.views.blueprint)
    import shop.cms.views
    app.register_blueprint(shop.cms.views.blueprint)
    import shop.checkout.views
    app.register_blueprint(shop.checkout.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_context_processors(app):
    app.context_processor(lambda: {
        'current_channel': current_channel,
        'current_app': current_app,
    })
