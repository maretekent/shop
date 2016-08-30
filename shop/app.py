# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask

from shop import node, product, public, user
from shop.assets import assets
from shop.extensions import (babel, cache, csrf_protect, debug_toolbar, fulfil, login_manager, redis_store, sentry,
                             themes)
from shop.fulfilio import channel
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
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(product.views.blueprint)
    app.register_blueprint(node.views.blueprint)
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
    app.context_processor(lambda: {'channel': channel})
