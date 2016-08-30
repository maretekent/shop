# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint
from flask_login import login_required

from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'user', __name__,
    url_prefix='/my', static_folder='../static'
)


@blueprint.route('/addresses')
@login_required
def addresses():
    """List Addresses."""
    return render_template('users/addresses.html')
