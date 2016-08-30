# -*- coding: utf-8 -*-
"""
Helper utilities and decorators.
"""
from email import Charset, Encoders
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase

from flask import current_app, flash, render_template
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
