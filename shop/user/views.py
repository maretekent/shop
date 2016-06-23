# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint
from shop.utils import render_theme_template as render_template
from flask_login import login_required

blueprint = Blueprint(
    'user', __name__,
    url_prefix='/users', static_folder='../static'
)


@blueprint.route('/')
@login_required
def members():
    """List members."""
    return render_template('users/members.html')
