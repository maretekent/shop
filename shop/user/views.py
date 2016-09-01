# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, request, url_for, flash
from flask_login import login_required, current_user
from werkzeug import redirect

from shop.user.forms import AddressForm
from shop.utils import render_theme_template as render_template
from shop.user.models import Address
from shop.utils import flash_errors


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


@blueprint.route("/addresses/new", methods=["GET", "POST"])
@login_required
def create_address():
    """
    Create an address for the current nereid_user
    GET
    ~~~
    Return an address creation form
    POST
    ~~~~
    Creates an address and redirects to the address view. If a next_url
    is provided, redirects there.
    """
    address_name = "" if current_user.is_anonymous else \
        current_user.name
    form = AddressForm(request.form, name=address_name)

    if form.validate_on_submit():
        address = Address(party=current_user.party)
        form.populate_obj(address)
        address.save()
        flash("The new address has been added to your address book", 'success')
        return redirect(url_for('user.addresses'))

    return render_template('users/address-form.html', form=form)
