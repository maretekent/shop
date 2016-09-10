# -*- coding: utf-8 -*-
"""Product views."""
from flask import Blueprint, flash, redirect, request, url_for
from shop.cart.forms import AddtoCartForm
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
        flash('Product has been added to cart', 'success')
        return redirect(url_for('cart.view_cart'))
    flash('Could not add product to cart.', 'error')
    return redirect(request.referer)
