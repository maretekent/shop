# -*- coding: utf-8 -*-
"""Checkout views."""
import stripe
from flask import Blueprint, flash, redirect, request, session, url_for
from flask_login import current_user, login_user, login_required
from shop.cart.models import Sale
from shop.checkout.forms import CheckoutAddressForm, CheckoutSignInForm
from shop.checkout.models import (PaymentProfile, not_empty_cart,
                                  sale_has_non_guest_party)
from shop.globals import current_cart, current_channel, current_app
from shop.user.models import Address, Party, User
from shop.utils import render_theme_template as render_template
from shop.signals import cart_user_changed

blueprint = Blueprint(
    'checkout', __name__,
    url_prefix='/checkout', static_folder='../static'
)


@blueprint.route('/sign-in', methods=["GET", "POST"])
@not_empty_cart
def sign_in():
    if not current_user.is_anonymous:
        # Registered user with a fresh login can directly proceed to
        # step 2, which is filling the shipping address
        #
        # if this is a recent sign-in by a registered user
        # automatically proceed to the shipping_address step
        # TODO: Check if this is a recent login
        return redirect(url_for('checkout.shipping_address'))

    form = CheckoutSignInForm(
        email=session.get('email'),
        checkout_mode='guest',
    )

    if form.validate_on_submit():
        if form.checkout_mode.data == 'guest':
            existing_user = User.find_user(form.email.data)
            if existing_user:
                if not existing_user.active:
                    flash("Please activate your account first")
                else:
                    return render_template(
                        'checkout/signin-email-in-use.html',
                        email=form.email.data
                    )

            cart = current_cart
            party_name = unicode('Guest with email: %s' % form.email.data)
            if cart.sale.party.id == current_channel.anonymous_customer.id:
                # Create a party with the email as email, and session as
                # name, but attach the session to it.
                party, = Party.rpc.create([{
                    'name': party_name,
                    'nereid_session': session.sid,
                    'addresses': [],
                    'contact_mechanisms': [('create', [{
                        'type': 'email',
                        'value': form.email.data,
                    }])]
                }])

                sale = cart.sale
                sale.party = party
                sale.save()
            else:
                # Perhaps the email changed ?
                party = cart.sale.party
                party.name = party_name

                # contact_mechanism of email type will always be there for
                # Guest user
                contact_mechanism = filter(
                    lambda c: c.type == 'email', party.contact_mechanisms
                )[0]
                contact_mechanism.value = form.email.data
                contact_mechanism.save()
                party.email = form.email.data
                party.save()

            cart_user_changed.send(current_app._get_current_object())

            return redirect(
                url_for('checkout.shipping_address')
            )
        else:
            # The user wants to use existing email to login
            user = User.authenticate(
                form.email.data, form.password.data
            )
            if user:
                login_user(user)
                return redirect(
                    url_for('checkout.shipping_address')
                )
            else:
                return redirect(request.referrer)

    return render_template(
        'checkout/sign_in.html',
        form=form,
    )


@blueprint.route('/shipping-address', methods=['GET', 'POST'])
@not_empty_cart
@sale_has_non_guest_party
def shipping_address():
    cart = current_cart

    address = None
    if current_user.is_anonymous and cart.sale.shipment_address:
        address = cart.sale.shipment_address

    address_form = CheckoutAddressForm(object=address)
    if address_form.validate_on_submit():
        if address_form.address.data:
            # Registered user has chosen an existing address
            address = Address.get_by_id(address_form.address.data)

        else:
            # Guest user or registered user creating an address. Only
            # difference is that the party of address depends on guest or
            # not
            if current_user.is_anonymous and \
                    cart.sale.shipment_address:
                # Save to the same address if the guest user
                # is just trying to update the address
                address = cart.sale.shipment_address
            else:
                address = Address()

            address.party = cart.sale.party.id
            address.name = address_form.name.data
            address.street = address_form.street.data
            address.streetbis = address_form.streetbis.data
            address.zip = address_form.zip.data
            address.city = address_form.city.data
            address.country = address_form.country.data
            address.subdivision = address_form.subdivision.data

            if address_form.phone.data:
                address.phone = address_form.phone.data
            address.save()

        if address is not None:
            sale = cart.sale
            sale.shipment_address = address.id
            sale.invoice_address = address.id
            sale.save()

            return redirect(
                url_for('checkout.validate_address')
            )

    addresses = []
    if not current_user.is_anonymous:
        addresses.extend(current_user.party.addresses)

    return render_template(
        'checkout/shipping_address.html',
        addresses=addresses,
        address_form=address_form,
    )


@blueprint.route('/validate-address', methods=['GET', 'POST'])
@not_empty_cart
@sale_has_non_guest_party
def validate_address():
    return redirect(url_for('checkout.delivery_method'))


@blueprint.route('/delivery-method', methods=['GET', 'POST'])
@not_empty_cart
@sale_has_non_guest_party
def delivery_method():
    return redirect(url_for('checkout.payment'))


@blueprint.route('/payment', methods=['GET', 'POST'])
@not_empty_cart
@sale_has_non_guest_party
def payment():
    cart = current_cart
    if not cart.sale.shipment_address:
        return redirect(url_for('checkout.shipping_address'))
    if request.method == 'POST':
        try:
            customer_id = PaymentProfile.rpc.create_profile_using_stripe_token(
                current_user.party.id,
                current_channel.payment_gateway.id,
                request.form.get('stripeToken')
            )
            Sale.rpc.add_sale_payment(
                current_cart.sale.id,
                current_channel.payment_gateway.id,
                customer_id
            )
        except stripe.error.CardError:
            # The card has been declined
            flash("Your Card has been declined, please try again later")
            return redirect(request.referrer)
        else:
            # Save sale to a local variable as confirm method clears the sale
            sale = cart.sale
            cart.confirm()
            return redirect(url_for(
                'checkout.order',
                sale_id=sale.id,
                confirmation=True,
                access_code=sale.guest_access_code,
            ))

    return render_template(
        'checkout/payment.html'
    )

@login_required
@blueprint.route('/order/<int:sale_id>')
def order(sale_id):
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
        'checkout/order-confirmation.html', sale=sale, confirmation=confirmation
    )
