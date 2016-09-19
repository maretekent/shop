# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, flash, redirect, request, url_for
from flask_babel import gettext as _
from flask_login import current_user
from shop.cart.forms import AddtoCartForm, RemoveFromCartForm
from shop.cart.models import Cart, Sale
from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'cart', __name__,
    url_prefix='/cart', static_folder='../static'
)


@blueprint.route('/')
def view_cart():
    "Display shopping cart"
    cart = Cart.get_active()
    return render_template(
        'cart/cart.html',
        cart=cart,
    )


@blueprint.route('/add', methods=["POST"])
def add_to_cart():
    "Add product to cart"
    form = AddtoCartForm(request.form)
    cart = Cart.get_active()
    if form.validate_on_submit():
        cart.add_product(
            product_id=form.product.data,
            quantity=form.quantity.data
        )
        flash(_('Product has been added to cart'), 'success')
        return redirect(url_for('cart.view_cart'))
    flash('Could not add product to cart.', 'error')
    return redirect(request.referrer)


@blueprint.route('/remove', methods=['POST'])
def remove_from_cart():
    form = RemoveFromCartForm(request.form)
    cart = Cart.get_active()
    if form.validate_on_submit():
        cart.remove_sale_line(
            line_id=form.line_id.data
        )
        flash(_("Removed product from cart"), 'success')
        return redirect(url_for('cart.view_cart'))
    flash(_('Looks like the item is already deleted.'), 'error')
    return redirect(request.referrer)


@blueprint.route('/empty', methods=['POST'])
def empty_cart():
    """
    Empties the cart
    """
    cart = Cart.get_active()
    cart.clear()
    return redirect(url_for('cart.view_cart'))


@blueprint.route('/order/<int:sale_id>')
def render(sale_id):
    """Render given sale order
    :param sale: ID of the sale Order
    """
    confirmation = request.values.get('confirmation', type=bool)
    # Try to find if the user can be shown the order
    access_code = request.values.get('access_code', None)
    sale = Sale.get_by_id(sale_id)

    if current_user.is_anonymous:
        if not access_code:
            # No access code provided, user is not authorized to
            # access order page
            abort(401)
        if access_code != sale.guest_access_code:
            # Invalid access code
            abort(403)
    else:
        if sale.party.id != current_user.party.id:
            # Order does not belong to the user
            abort(403)

    return render_template(
        'cart/order-confirmation.html', sale=sale, confirmation=confirmation
    )
