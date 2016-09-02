# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, request, flash, url_for, abort
from flask_login import login_required, current_user
from werkzeug import redirect

from shop.user.forms import AddressForm
from shop.utils import render_theme_template as render_template
from shop.user.models import Address

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


@blueprint.route("/address/edit/<int:address_id>", methods=["GET", "POST"])
@login_required
def edit_address(address_id):
    """
    Edit an Address
    POST will update an existing address.
    GET will return a existing address edit form.
    :param address_id: ID of the address
    """
    address = Address.query.get(address_id)
    if not address.party == current_user.party:
        abort(403)

    form = AddressForm(request.form, address)
    if form.validate_on_submit():
        form.populate_obj(address)
        address.party = current_user.party
        address.save()
        flash('Address successfully updated', 'success')
        return redirect(url_for('user.addresses'))

    return render_template('users/address-edit.html', form=form, address=address)


@blueprint.route("/address/delete/<int:address_id>", methods=["POST"])
@login_required
def delete_address(address_id):
    """
    Delete an address
    POST deletes the address with the address_id
    """
    address_query = Address.query.filter_by(id=address_id)
    if (address_query.all()[0]):
        # If there was an address returned
        address_query.archive()
        flash("Address deleted", 'warning')
        return redirect(url_for('user.addresses'))
    else:
        abort(404)
