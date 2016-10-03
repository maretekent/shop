# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, abort, flash, redirect, request, url_for, jsonify
from flask_babel import gettext as _, format_currency, format_number
from flask_login import current_user, login_required
from shop.cart.forms import AddtoCartForm, RemoveFromCartForm
from shop.cart.models import Cart
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
        if not cart.sale:
            return jsonify({'empty': True})

        ccy = cart.sale.currency_code
        return jsonify({
            'cart': {
                'lines': [{
                    'product': l.product and l.product.name or None,
                    'quantity': format_number(l.quantity),
                    'unit': l.unit.symbol,
                    'unit_price': format_currency(l.unit_price, ccy),
                    'amount': format_currency(l.amount, ccy),
                } for l in cart.sale.lines],
                'empty': len(cart.sale.lines) > 0,
                'total_amount': format_currency(cart.sale.total_amount, ccy),
                'tax_amount': format_currency(cart.sale.tax_amount, ccy),
                'untaxed_amount': format_currency(cart.sale.untaxed_amount, ccy),
            }
        })
    return render_template('cart/cart.html', cart=cart)


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
