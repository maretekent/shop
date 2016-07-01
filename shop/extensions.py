# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_fulfil import Fulfil
from flask_login import LoginManager
from flask_wtf.csrf import CsrfProtect
from flask.ext.themes2 import Themes
from raven.contrib.flask import Sentry

csrf_protect = CsrfProtect()
login_manager = LoginManager()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
fulfil = Fulfil()
themes = Themes()
sentry = Sentry()
