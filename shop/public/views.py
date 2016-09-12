# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   request, url_for)
from flask_babel import gettext as _
from flask_login import login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired

from shop.extensions import login_manager
from shop.public.forms import LoginForm, NewPasswordForm, ResetPasswordForm
from shop.public.models import Country, Banner
from shop.user.forms import RegisterForm
from shop.user.models import User
from shop.utils import render_theme_template as render_template
from shop.utils import flash_errors

blueprint = Blueprint('public', __name__, static_folder='../static')


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Home page."""
    banners = Banner.query.filter_by_domain(
        [
            ('category.name', '=', 'Home Page Banners')
        ]
    ).all()
    return render_template('public/home.html', banners=banners)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Login Page"""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash('You are logged in.', 'success')
            redirect_url = request.args.get('next') or url_for('public.home')
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/login.html', form=form)


@blueprint.route('/logout/')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route('/register/', methods=['GET', 'POST'])
def register():
    """Register new user."""
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            active=True
        ).save()
        flash('Thank you for registering. You can now log in.', 'success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)


@blueprint.route('/about/')
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template('public/about.html', form=form)


@blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        form.user.initiate_reset_password()
        return render_template('public/reset-password-sent.html')
    return render_template('public/reset-password.html', form=form)


@blueprint.route('/new-password/<int:user_id>/<sign>', methods=['GET', 'POST'])
def new_password(user_id, sign, max_age=60 * 60):
    form = NewPasswordForm()
    if form.validate_on_submit():
        try:
            unsigned = User._serializer().loads(
                User._signer().unsign(sign, max_age=max_age),
                salt='reset-password'
            )
        except SignatureExpired:
            return xhr_safe_response(
                _('The password reset link has expired'),
                redirect(url_for('public.reset_password')), 400
            )
        except BadSignature:
            return xhr_safe_response(
                _('Invalid reset password code'),
                redirect(url_for('public.reset_password')), 400
            )
        else:
            if not user_id == unsigned:
                current_app.logger.debug('Invalid reset password code')
                abort(403)

            User.get_by_id(user_id).set_password(form.password.data)
            return xhr_safe_response(
                'Your password has been successfully changed! '
                'Please login again',
                redirect(url_for('public.login')), 200
            )
    elif form.errors and (request.is_xhr or request.is_json):
            return jsonify(errors=form.errors), 400
    return render_template('public/new-password.html', form=form)


@blueprint.route('/countries')
def get_countries():
    countries = Country.get_list()
    response = {
        "result":
        [{"id": c.id,
          "name": c.name,
          "code": c.code}
         for c in countries]
    }
    return jsonify(response)


@blueprint.route('/countries/<int:country_id>/subdivisions')
def get_country_subdivisions(country_id):
    country = Country(id=country_id)
    subdivisions = country.subdivisions
    response = {
        "result":
        [{"name": s.name,
          "id": s.id}
            for s in subdivisions]
    }
    return jsonify(response)


def xhr_safe_response(message, response, xhr_status_code):
    """
    Method to handle response for jinja and XHR requests.
    message: Message to show as flash and send as json response.
    response: redirect or render_template method.
    xhr_status_code: Status code to be sent with json response.
    """
    if request.is_xhr or request.is_json:
        return jsonify(message=message), xhr_status_code
    flash(_(message))
    return response
