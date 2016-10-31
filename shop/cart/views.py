# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, flash, redirect, request, url_for, jsonify
from flask_babel import gettext as _, format_currency, format_number
from flask_login import current_user, login_required
from shop.cart.forms import AddtoCartForm, RemoveFromCartForm, \
    UpdateShippingAddressForm, UpdateShippingDateForm, UpdateGiftMessageForm
from shop.cart.models import Cart
from shop.globals import current_context
from shop.utils import render_theme_template as render_template

blueprint = Blueprint(
    'cart', __name__,
    url_prefix='/cart', static_folder='../static'
)


@blueprint.route('/')
def view_cart():
    "Display shopping cart"
    cart = Cart.get_active()
    if request.is_xhr or request.is_json:
        return jsonify({'cart': cart.serialize()})
    return render_template('cart/cart.html', cart=cart)


@blueprint.route('/add', methods=["POST"])
def add_to_cart():
    "Add product to cart"
    form = AddtoCartForm(request.form)
    cart = Cart.get_active()
    if form.validate_on_submit():
        cart.add_product(
            product_id=form.product.data,
            quantity=form.quantity.data,
            delivery_date=form.delivery_date.data,
            address_id=form.address_id.data,
        )
        if request.is_xhr or request.is_json:
            return jsonify({"message": "Item successfully added to cart."})
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
        if request.is_xhr or request.is_json:
            return jsonify({"message": "Item successfully removed from cart."})

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
    if request.is_xhr or request.is_json:
        return jsonify({"message": "Cart successfully emptied."})
    return redirect(url_for('cart.view_cart'))


@blueprint.route('/update-shipping-address', methods=['POST'])
def update_shipping_address():
    form = UpdateShippingAddressForm()
    if form.validate_on_submit():
        cart = Cart.get_active()
        cart.update_shipping_address(
            form.line_id.data, form.address_id.data
        )
        if request.is_xhr or request.is_json:
            return jsonify({"message": "Shipping address updated."})
        flash(_("Address updated on item"), 'success')
        return redirect(url_for('cart.view_cart'))

    flash(_('Looks like address or item is invalid'), 'error')
    return redirect(request.referrer)


@blueprint.route('/update-shipping-date', methods=['POST'])
def update_delivery_date():
    form = UpdateShippingDateForm()
    if form.validate_on_submit():
        cart = Cart.get_active()
        cart.update_delivery_date(
            form.line_id.data, form.delivery_date.data
        )
        if request.is_xhr or request.is_json:
            return jsonify({"message": "Shipping date updated."})
        flash(_("Shipping date updated on item"), 'success')
        return redirect(url_for('cart.view_cart'))
    flash(_('Looks like date or item is invalid'), 'error')
    return redirect(request.referrer)


@blueprint.route('/update-gift-message', methods=['POST'])
def update_gift_message():
    form = UpdateGiftMessageForm()
    if form.validate_on_submit():
        cart = Cart.get_active()
        cart.update_gift_message(
            form.line_id.data, form.gift_message.data
        )
        flash(_("Gift message has been updated on item"), 'success')
        if request.is_xhr or request.is_json:
            return jsonify({"message": "Gift message updated."})
        return redirect(url_for('cart.view_cart'))
    flash(_('Looks like item is invalid'), 'error')
    return redirect(request.referrer)
