# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint
from flask_login import login_required, current_user

from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'user', __name__,
    url_prefix='/my', static_folder='../static'
)


@blueprint.route('/addresses')
@login_required
def addresses():
    """List Addresses."""
    addresses = current_user.get_addresses()
    return render_template('users/addresses.html', addresses=addresses)
