# -*- coding: utf-8 -*-
"""
Helper utilities and decorators.
"""
from math import ceil
import simplejson as json

from email import Charset, Encoders
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase

from flask import current_app, flash, render_template, url_for, request
from flask.ext.themes2 import render_theme_template as rtt
from flask.ext.themes2 import get_theme
from premailer import transform

# Override python's weird assumption that utf-8 text should be encoded with
# base64, and instead use quoted-printable (for both subject and body).  I
# can't figure out a way to specify QP (quoted-printable) instead of base64 in
# a way that doesn't modify global state. :-(
#
# wordeology.com/computer/how-to-send-good-unicode-email-with-python.html
Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(
                getattr(form, field).label.text, error), category
            )


def get_current_theme():
    """
    Return the identifier of the current theme.
    """
    ident = current_app.config.get('THEME', 'default')
    return get_theme(ident)


def render_theme_template(*args, **kwargs):
    """
    Render the template using current theme.
    """
    return rtt(get_current_theme(), *args, **kwargs)


def get_random_product():
        import random
        from shop.product.models import Product
        p_images = [
            "https://cdn.shopify.com/s/files/1/0533/3153/products/1-1_large.jpg?v=1404837242",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2405/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/682/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2357/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/2356/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/386/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
            "https://dzhj8173mkary.cloudfront.net/static-file-transform/388/thumbnail%2Cw_300%2Ch_300%2Cm_a.jpg",
        ]
        dummy_products = [
            Product(uri='tp1', name='Product 1', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 2', price="$40.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product long one 3', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 4', price="$140.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 5', price="$10,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 6', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product longer longer 7', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 8', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 9', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 10', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 11', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 12', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 13', price="$1,040.00", image=random.choice(p_images)),
            Product(uri='tp1', name='Product 14', price="$1,040.00", image=random.choice(p_images)),
        ]
        return random.choice(dummy_products)


def dummy_products(func):
    def wrapper(*args, **kwargs):
        dummy_products = [
            get_random_product() for c in range(15)
        ]
        return dummy_products
    return wrapper


def render_email(
        from_email, to, subject, text_template=None, html_template=None,
        cc=None, attachments=None, **context):
    """
    Read the templates for email messages, format them, construct
    the email from them and return the corresponding email message
    object.

    :param from_email: Email From
    :param to: Email IDs of direct recepients (list)
    :param subject: Email subject
    :param text_template: name of text template
    :param html_template: name of html template
    :param cc: Email IDs of Cc recepients (list)
    :param attachments: A dict of filename:string as key value pair
                        [preferable file buffer streams]
    :param context: Context to be sent to template rendering
    :return: Email multipart instance or Text/HTML part
    """
    if not (text_template or html_template):
        raise Exception("Atleast HTML or TEXT template is required")

    text_part = None
    if text_template:
        text = unicode(render_template(text_template, **context))
        text_part = MIMEText(text.encode("utf-8"), 'plain', _charset="UTF-8")

    html_part = None
    if html_template:
        html = unicode(
            transform(render_template(html_template, **context))
        )
        html_part = MIMEText(html.encode("utf-8"), 'html', _charset="UTF-8")

    if text_part and html_part:
        # Construct an alternative part since both the HTML and Text Parts
        # exist.
        message = MIMEMultipart('alternative')
        message.attach(text_part)
        message.attach(html_part)
    else:
        # only one part exists, so use that as the message body.
        message = text_part or html_part

    if attachments:
        # If an attachment exists, the MimeType should be mixed and the
        # message body should just be another part of it.
        message_with_attachments = MIMEMultipart('mixed')

        # Set the message body as the first part
        message_with_attachments.attach(message)

        # Now the message _with_attachments itself becomes the message
        message = message_with_attachments

        for filename, content in attachments.items():
            part = MIMEBase('application', "octet-stream")
            part.set_payload(content)
            Encoders.encode_base64(part)
            # XXX: Filename might have to be encoded with utf-8,
            # i.e., part's encoding or with email's encoding
            part.add_header(
                'Content-Disposition', 'attachment; filename="%s"' % filename
            )
            message.attach(part)

    # If list of addresses are provided for to and cc, then convert it
    # into a string that is "," separated.
    if isinstance(to, (list, tuple)):
        to = ', '.join(to)
    if isinstance(cc, (list, tuple)):
        cc = ', '.join(cc)

    # We need to use Header objects here instead of just assigning the strings
    # in order to get our headers properly encoded (with QP).
    message['Subject'] = Header(unicode(subject), 'ISO-8859-1')
    message['From'] = Header(unicode(from_email), 'ISO-8859-1')
    message['To'] = Header(unicode(to), 'ISO-8859-1')
    if cc:
        message['Cc'] = Header(unicode(cc), 'ISO-8859-1')

    return message


def imgixify(images):
    "Replace fulfil cdn url with imgix cdn"
    imgix_cdn = current_app.config.get('IMGIX_CDN')
    if not imgix_cdn:
        return images

    fulfil_subdomain = current_app.config.get('FULFIL_SUBDOMAIN')
    fulfil_cdn = 'https://cdn.fulfil.io/%s' % fulfil_subdomain

    res = []
    for image in images:
        res.append(image.replace(fulfil_cdn, imgix_cdn, 1))
    return res


def cdnify(url):
    "CDNify a url"
    cdn_url = current_app.config.get('CDN')
    version = current_app.config.get('VERSION')
    if not url or not url.startswith('/'):
        # Only urls relative to root can be changes
        return url

    if cdn_url:
        url = "%s%s" % (cdn_url, url)
    if version:
        # TODO: Handle query params in url
        url += '?version=%s' % version
    return url


class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


class json_ld_dict(dict):
    def __html__(self):
        return (
            """<script type="application/ld+json">{0}</script>"""
        ).format(json.dumps(self))
