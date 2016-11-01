# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, abort, current_app, flash, jsonify, make_response,
                   redirect, request, url_for, make_response)
from flask_babel import gettext as _
from flask_login import login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired
from shop.extensions import fulfil, login_manager
from shop.globals import current_channel
from shop.product.models import ChannelListing
from shop.public.forms import LoginForm, NewPasswordForm, ResetPasswordForm
from shop.public.models import Banner, Country
from shop.user.forms import RegisterForm
from shop.user.models import User
from shop.utils import render_theme_template as render_template
from shop.utils import flash_errors, render_email

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
            ('category.name', '=', 'Home Page Banners'),
            ('state', '=', 'published')
        ]
    ).all()
    return render_template('public/home.html', banners=banners)


@blueprint.route('/shop.js')
def shop_js():
    """
    A Javascript utility file that has to be rendered.
    Done this way because it needs url_for
    """
    response = make_response(render_template('shop.js'))
    response.headers.set('Content-Type', 'application/javascript')
    return response


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Login Page"""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            if request.is_xhr or request.is_json:
                return jsonify({
                    'message': 'You are logged in.'
                })
            flash('You are logged in.', 'success')
            redirect_url = request.args.get('next') or url_for('public.home')
            return redirect(redirect_url)
        else:
            if request.is_xhr or request.is_json:
                return jsonify({
                    'errors': form.errors
                }), 400
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
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            active=True
        )
        user.save()
        login_user(user)
        flash('Thank you for registering. You are now logged in.', 'success')
        return redirect(request.values.get('next', request.referrer))
    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)


@blueprint.route('/search')
def search():
    """
    Lists results matching search query
    """
    # Only returns products as of now
    q = request.args.get('q')
    page = request.args.get('page', type=int) or None
    per_page = request.args.get('per_page', type=int) or None
    shop_query = ChannelListing.get_shop_query().filter_by_domain(
        [
            ('channel', '=', current_channel.id),
            ('product.active', '=', True),
            ('product.salable', '=', True),
            ('product.rec_name', 'ilike', '%{}%'.format(q)),
        ],
    )
    results = shop_query.paginate(page=page, per_page=per_page)
    return render_template('public/search.html', results=results)


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
                _('Your password has been successfully changed! '
                  'Please login again'),
                redirect(url_for('public.login')), 200
            )
    elif form.errors and (request.is_xhr or request.is_json):
            return jsonify(errors=form.errors), 400
    return render_template('public/new-password.html', form=form)


@blueprint.route("/magic-login/<int:user_id>/<sign>", methods=["GET"])
def magic_login(user_id, sign, max_age=5 * 60):
    """
    Let the user log in without password if the token
    is valid (less than 5 min old)
    """
    try:
        unsigned = User._serializer().loads(
            User._signer().unsign(sign, max_age=max_age),
            salt='magic-login'
        )
    except SignatureExpired:
        return xhr_safe_response(
            _('The link has expired'),
            redirect(url_for('public.login')), 400
        )
    except BadSignature:
        return xhr_safe_response(
            _('Invalid login link'),
            redirect(url_for('public.login')), 400
        )
    else:
        if not user_id == unsigned:
            current_app.logger.debug('Invalid link')
            abort(403)

        login_user(load_user(user_id))
        # TODO: Set this used token as expired to prevent using
        # it more than once
        return xhr_safe_response(
            _('You have been successfully logged in'),
            redirect(url_for('public.home')), 200
        )


@blueprint.route('/send-magic-link/<email>', methods=['GET'])
def send_magic_login_link(email):
    """
    Send a magic login email to the user
    """
    EmailQueue = fulfil.model('email.queue')

    user = User.query.filter_by_domain([
        ('email', '=', email),
    ]).first()
    if not user:
        # This email was not found so, let user know about this
        message = "No user with email %s was found!" % email
        current_app.logger.debug(_(message))
    else:
        message = "Please check your mail and follow the link"
        email_message = render_email(
            current_channel.support_email,  # From
            email, _('Magic Signin Link'),
            text_template='emails/magic-login-text.txt',
            html_template='emails/magic-login-html.html',
            user=user,
            channel=current_channel,
        )
        EmailQueue.create([{
            'from_addr': current_channel.support_email,
            'to_addrs': email,
            'msg': email_message.as_string()
        }])

    return xhr_safe_response(
        _(message), redirect(url_for('public.home')), 200
    )


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


@blueprint.route('/countries/<country_code>/subdivisions')
def get_country_subdivisions(country_code):
    country = Country.from_code(country_code)
    response = {
        "result": [
            {"name": s.name, "code": s.code, "id": s.id}
            for s in country.subdivisions
        ]
    }
    return jsonify(response)


@blueprint.route('/sitemap-index.xml')
def sitemap_index():
    """
    Returns a Sitemap Index Page
    """
    sitemap_xml = render_template('public/sitemap-index.xml')
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response


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
