# -*- coding: utf-8 -*-
"""Application configuration."""
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('SHOP_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    SESSION_TYPE = 'redis'  # Can be redis, memcached, mongodb, sqlalchemy

    FULFIL_SUBDOMAIN = os.environ.get('FULFIL_SUBDOMAIN')
    FULFIL_API_KEY = os.environ.get('FULFIL_API_KEY')
    FULFIL_CHANNEL = os.environ.get('FULFIL_CHANNEL')

    # IMGIX CDN https://example.imgix.net
    IMGIX_CDN = os.environ.get('IMGIX_CDN')

    # CDN https://iu23hu823i.cloudfront.net
    CDN = os.environ.get('FULFIL_SHOP_CDN')

    # Current version of shop
    # Used in logs and cache invalidation
    VERSION = os.environ.get('FULFIL_SHOP_VERSION')

    # Google tag manager
    GOOGLE_TAG_MANAGER = os.environ.get('GOOGLE_TAG_MANAGER')

    # Google tag manager
    GOOGLE_MAPS_API_TOKEN = os.environ.get('GOOGLE_MAPS_API_TOKEN')

    if 'FULFIL_ROOT_NAV' in os.environ:
        FULFIL_ROOT_NAV = os.environ['FULFIL_ROOT_NAV']
    if 'FULFIL_FOOTER_NAV' in os.environ:
        FULFIL_FOOTER_NAV = os.environ['FULFIL_FOOTER_NAV']

    REDIS_URL = 'redis://redis:6379/0'
    if 'REDIS_URL' in os.environ:
        REDIS_URL = os.environ.get('REDIS_URL')
    # Cache expiry in seconds. By default 10 minutes
    REDIS_EX = int(os.environ.get('REDIS_EX', 10 * 60))
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_IMPORTS = [
        'shop.jobs'
    ]

    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

    THEME = 'default'
    THEME_PATHS = [
        os.path.join(APP_DIR, 'themes/'),
    ]


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar

    # Cache files for 24 hours
    SEND_FILE_MAX_AGE_DEFAULT = 60 * 60 * 24


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_ENABLED = True
    ASSETS_DEBUG = True  # Don't bundle/minify static assets
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4  # For faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
    WTF_CSRF_ENABLED = False  # Allows form testing
