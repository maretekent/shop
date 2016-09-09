# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask.ext.themes2 import Themes
from flask_babel import Babel
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_fulfil import Fulfil
from flask_login import LoginManager
from flask_redis import FlaskRedis
from flask_session import Session
from flask_wtf.csrf import CsrfProtect
from raven.contrib.flask import Sentry
from redis import StrictRedis

csrf_protect = CsrfProtect()
login_manager = LoginManager()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
fulfil = Fulfil()
themes = Themes()
sentry = Sentry()
babel = Babel()
redis_store = FlaskRedis.from_custom_provider(StrictRedis)
session = Session()
