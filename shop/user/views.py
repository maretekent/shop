# -*- coding: utf-8 -*-
"""User views."""
from datetime import date

from dateutil.relativedelta import relativedelta
from flask import Blueprint, flash, request, url_for
from flask_login import current_user, login_required
from werkzeug import redirect

from shop.cart.models import Sale
from shop.user.forms import AddressForm, ChangePasswordForm
from shop.user.models import Address
from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'user', __name__,
    url_prefix='/my', static_folder='../static'
)


@blueprint.route('/change-password', methods=["GET", "POST"])
@login_required
def change_password():
    """
    Change user's password
    """
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        flash("Your password was successfully updated!", "success")
        return redirect(url_for('public.home'))
    return render_template('users/change-password.html', form=form)


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


@blueprint.route('/orders')
@login_required
def orders():
    """Render all orders
    """
    filter_by = request.args.get('filter_by', None)
    page = request.args.get('page', type=int) or None
    per_page = request.args.get('per_page', type=int) or 24

    domain = [
        ('party', '=', current_user.party.id),
    ]
    req_date = (
        date.today() + relativedelta(months=-3)
    )

    if filter_by == 'done':
        domain.append(('state', '=', 'done'))

    elif filter_by == 'canceled':
        domain.append(('state', '=', 'cancel'))

    elif filter_by == 'archived':
        # only done and cancelled orders should be in archive
        # irrespective of the date. Pre orders for example
        # could be over 3 months old and still be in the
        # processing state
        domain.append(
            ('state', 'in', ('done', 'cancel'))
        )

        # Add a sale_date domain for recent orders.
        domain.append((
            'sale_date', '<', req_date
        ))

    else:
        domain.append([
            'OR',
            ('state', 'in', ('confirmed', 'processing')),
            [
                ('state', 'in', ('done', 'cancel')),
                ('sale_date', '>=', req_date),
            ]
        ])

    # Handle order duration
    shop_query = Sale.get_shop_query().filter_by_domain(domain)
    paginate = shop_query.paginate(page=page, per_page=per_page)

    return render_template(
        'users/orders.html',
        sales=paginate.items,
        paginate=paginate
    )
