# -*- coding: utf-8 -*-
"""
Fulfil.IO Utils.

Helper data structures and API wrappers to make it easier to access RPC
from views and models.
"""
from math import ceil

from flask import abort, current_app, has_request_context, request
from werkzeug.local import LocalProxy

from fulfil_client.model import Query, StringType, model_base
from shop.extensions import fulfil, redis_store

Model = model_base(fulfil, redis_store)


class Channel(Model):
    __model_name__ = 'sale.channel'

    name = StringType()
    # support_email = StringType()

    @property
    def support_email(self):
        # TODO: Add support email to channel
        # This is a temporary hack until then
        import os
        return os.environ['FROM_EMAIL']

    @classmethod
    def get_current_channel(cls):
        "Get the current channel based on the env var"
        return Channel.from_cache(
            current_app.config['FULFIL_CHANNEL']
        )


channel = LocalProxy(Channel.get_current_channel)


class ShopQuery(Query):
    """
    Implement web specific methods before starting to use query
    """

    def get_or_404(self, ident):
        """
        Like :meth:`get` but aborts with 404 if not found instead
        of returning ``None``.
        """
        rv = self.get(ident)
        if rv is None:
            abort(404)
        return rv

    def first_or_404(self):
        """
        Like :meth:`first` but aborts with 404 if not found instead
        of returning ``None``.
        """
        rv = self.first()
        if rv is None:
            abort(404)
        return rv

    def paginate(self, page=None, per_page=None, error_out=True):
        """
        Returns ``per_page`` items from page ``page``.

        If no items are found and ``page`` is greater than 1
        or if page is less than 1, it aborts with 404.
        This behavior can be disabled by passing ``error_out=False``.

        If ``page`` or ``per_page`` are ``None``, they will be retrieved
        from the request query.
        If the values are not ints and ``error_out`` is ``True``,
        it aborts with 404.
        If there is no request or they aren't in the query,
        they default to 1 and 20 respectively.

        Returns a :class:`Pagination` object.
        """
        if has_request_context():
            if page is None:
                try:
                    page = int(request.args.get('page', 1))
                except (TypeError, ValueError):
                    if error_out:
                        abort(404)

                    page = 1

            if per_page is None:
                try:
                    per_page = int(request.args.get('per_page', 20))
                except (TypeError, ValueError):
                    if error_out:
                        abort(404)

                    per_page = 20
        else:
            if page is None:
                page = 1

            if per_page is None:
                per_page = 20

        if error_out and page < 1:
            abort(404)

        items = self.limit(per_page).offset((page - 1) * per_page).all()

        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        u"""
        Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>…</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
