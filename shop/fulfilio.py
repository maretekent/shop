# -*- coding: utf-8 -*-
"""
Fulfil.IO Utils.

Helper data structures and API wrappers to make it easier to access RPC
from views and models.
"""
import functools
from copy import copy
from math import ceil

import fulfil_client

from shop.extensions import fulfil
from flask import abort, has_request_context, request


class BaseType(object):
    """
    A django field like object that implements a descriptor.
    """
    # Eager load this field
    eager = True

    def __init__(self, cast, required=False, default=None):
        # this will be auto discovered by a meta class
        self.name = None

        self.cast = cast
        self.default = default
        self.required = required

    def __get__(self, instance, owner):
        if instance:
            return instance._values.get(self.name, self.default)
        else:
            return self

    def convert(self, value):
        return self.cast(value)

    def __set__(self, instance, value):
        instance._values[self.name] = self.convert(value)

    def __delete__(self, instance):
        del instance._values[self.name]


class IntType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', int)
        super(IntType, self).__init__(*args, **kwargs)


class BooleanType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', bool)
        super(BooleanType, self).__init__(*args, **kwargs)


class StringType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', unicode)
        super(StringType, self).__init__(*args, **kwargs)


class CurrencyType(StringType):
    pass


class ModelType(IntType):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(ModelType, self).__init__(*args, **kwargs)


class NamedDescriptorResolverMetaClass(type):
    """
    A metaclass that discovers field names
    """

    def __new__(cls, classname, bases, class_dict):
        if not class_dict.get('__abstract__') and \
                '__model_name__' not in class_dict:
            raise Exception('__name__ not defined for model')

        fields = class_dict.get('_fields', set([]))
        eager_fields = class_dict.get('_eager_fields', set([]))

        # Iterate through the new class' __dict__ to:
        #
        # * update all recognised NamedDescriptor member names
        # * find lazy loaded fields
        # * find eager_loaded fields
        for name, attr in class_dict.iteritems():
            if isinstance(attr, BaseType):
                attr.name = name
                fields.add(name)
                if attr.eager:
                    eager_fields.add(name)

        class_dict['_eager_fields'] = tuple(eager_fields)
        class_dict['_fields'] = tuple(fields | eager_fields)

        # Call super and continue class creation
        return type.__new__(cls, classname, bases, class_dict)


class ModificationTrackingDict(dict):
    """
    A change tracking dictionary
    """

    def __init__(self, *args, **kwargs):
        self.changes = set([])
        super(ModificationTrackingDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, val):
        if key not in self or self[key] != val:
            self.changes.add(key)
        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs):
        """
        Update does not call __setitem__ by default
        """
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v


def return_instances(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        query = args[0]
        results = function(*args, **kwargs)
        if query.instance_class:
            return map(query.instance_class, results)
        else:
            return results
    return wrapper


def return_instance(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        query = args[0]
        result = function(*args, **kwargs)
        if result is None:
            return None
        if query.instance_class:
            return query.instance_class(**result)
        else:
            return result
    return wrapper


class classproperty(object):    # NOQA
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class Query(object):
    """
    A sqlalchemy like query object giving developers familiar primitives.

    The method are limited to what are reasonable over an API.
    """

    def __init__(self, model, instance_class=None):
        self.rpc_model = model
        self.instance_class = instance_class or None
        self.domain = []
        self._limit = None
        self._offset = None
        self._order_by = None
        self.active_only = True

    @property
    def fields(self):
        return self.instance_class and self.instance_class._fields or None

    def __copy__(self):
        """
        Change the copy behavior of query.

        Maintain references to model and instance class while building a new
        list for domain and order by
        """
        newone = type(self)(self.rpc_model, self.instance_class)

        # immutable types
        newone._limit = self._limit
        newone._offset = self._offset
        newone.active_only = self.active_only

        # Duplicate the lists
        if self._order_by:
            newone._order_by = self._order_by[:]
        newone.domain = self.domain[:]
        return newone

    @property
    def context(self):
        "Return the context to execute the query"
        return {
            'active_test': self.active_only,
        }

    def _copy(self):
        "Internal method to make copies of the query"
        return copy(self)

    @return_instances
    def all(self):
        "Return the results represented by this Query as a list."
        return self.rpc_model.search_read(
            self.domain, self._limit, self._offset, self._order_by,
            self.fields,
            context=self.context
        )

    def count(self):
        "Return a count of rows this Query would return."
        return self.rpc_model.search_count(
            self.domain, context=self.context
        )

    def exists(self):
        """
        A convenience method that returns True if a record
        satisfying the query exists
        """
        return self.rpc_model.search_count(
            self.domain, context=self.context
        ) > 0

    def show_active_only(self, state):
        """
        Set active only to true or false on a copy of this query
        """
        query = self._copy()
        query.active_only = state
        return query

    def filter_by(self, **kwargs):
        """
        Apply the given filtering criterion to a copy of this Query, using
        keyword expressions.
        """
        query = self._copy()
        for field, value in kwargs.iteritems():
            query.domain.append(
                (field, '=', value)
            )
        return query

    def filter_by_domain(self, domain):
        """
        Apply the given domain to a copy of this query
        """
        query = self._copy()
        query.domain = domain
        return query

    @return_instance
    def first(self):
        """
        Return the first result of this Query or None if the result
        doesn't contain any row.
        """
        results = self.rpc_model.search_read(
            self.domain, None, 1, self._order_by, self.fields,
            context=self.context
        )
        return results and results[0] or None

    @return_instance
    def get(self, id):
        """
        Return an instance based on the given primary key identifier,
        or None if not found.

        This returns a record whether active or not.
        """
        ctx = self.context.copy()
        ctx['active_test'] = False
        results = self.rpc_model.search_read(
            [('id', '=', id)],
            None, None, None, self.fields,
            context=ctx
        )
        return results and results[0] or None

    def limit(self, limit):
        """
        Apply a LIMIT to the query and return the newly resulting Query.
        """
        query = self._copy()
        query._limit = limit
        return query

    def offset(self, offset):
        """
        Apply an OFFSET to the query and return the newly resulting Query.
        """
        query = self._copy()
        query._offset = offset
        return query

    @return_instance
    def one(self):
        """
        Return exactly one result or raise an exception.

        Raises fulfil_client.exc.NoResultFound if the query selects no rows.
        Raises fulfil_client.exc.MultipleResultsFound if multiple rows are
        found.
        """
        results = self.rpc_model.search_read(
            self.domain, 2, None, self._order_by, self.fields,
            context=self.context
        )
        if not results:
            raise fulfil_client.exc.NoResultFound
        if len(results) > 1:
            raise fulfil_client.exc.MultipleResultsFound
        return results[0]

    def order_by(self, *criterion):
        """
        apply one or more ORDER BY criterion to the query and
        return the newly resulting Query

        All existing ORDER BY settings can be suppressed by passing None -
        this will suppress any ORDER BY configured on mappers as well.
        """
        query = self._copy()
        query._order_by = criterion
        return query

    def delete(self):
        """
        Delete all records matching the query.

        Warning: This is a desctructive operation.

        Not every model allows deletion of records and several models
        even restrict based on status. For example, deleting products
        that have been transacted is restricted. Another example is sales
        orders which can be deleted only when they are draft.

        If deletion fails, a server error is thrown.
        """
        ids = self.rpc_model.search(self.domain, context=self.context)
        if ids:
            self.rpc_model.delete(ids)

    def archive(self):
        """
        Archives (soft delete) all the records matching the query.

        This assumes that the model allows archiving (not many do - especially
        transactional documents).

        Internal implementation sets the active field to False.
        """
        ids = self.rpc_model.search(self.domain, context=self.context)
        if ids:
            self.rpc_model.write(ids, {'active': False})


class Model(object):
    """
    Active record design pattern for RPC models.
    """

    __metaclass__ = NamedDescriptorResolverMetaClass
    __abstract__ = True

    id = IntType()

    def __init__(self, values=None, id=None, **kwargs):
        values = values or {}
        values.update(kwargs)

        if id is not None:
            values['id'] = id

        # Now create a modification tracking dictionary
        self._values = ModificationTrackingDict(values)

    @classmethod
    def from_ids(cls, ids):
        """
        Create multiple active resources at once
        """
        return map(cls, cls.rpc.read(ids, cls._eager_fields))

    @property
    def changes(self):
        """
        Return a set of changes
        """
        return dict([
            (field_name, self._values[field_name])
            for field_name in self._values.changes
        ])

    @classproperty
    def query(cls):     # NOQA
        return ShopQuery(cls.get_rpc_model(), cls)

    @property
    def has_changed(self):
        "Return True if the record has changed"
        return len(self._values) > 0

    @classproperty
    def rpc(cls):       # NOQA
        "Returns an RPC client for the Fulfil.IO model with same name"
        return cls.get_rpc_model()

    @classmethod
    def get_rpc_model(cls):
        "Returns an instance of the model record"
        return fulfil.model(cls.__model_name__)

    @classmethod
    def get_rpc_record(cls, id):
        "Returns an instance for Fulfil.IO Client Record"
        return fulfil.record(cls.__model_name__, id)

    @classmethod
    def get_by_id(cls, id):
        "Given an integer ID, fetch the record from fulfil.io"
        return cls(values=cls.rpc.read([id], cls._eager_fields)[0])

    def refresh(self):
        """
        Refresh a record by fetching again from the API.
        This also resets the modifications in the record.
        """
        assert self.id, "Cannot refresh unsaved record"
        self._values = ModificationTrackingDict(
            self.rpc.read([self.id], self._fields)[0]
        )

    def save(self):
        "Save as a new record if there is no id, or update record with id"
        if self.id:
            if self.changes:
                self.rpc.write([self.id], self.changes)
        else:
            self.id = self.rpc.create([self._values])[0]

        # Either way refresh the record after saving
        self.refresh()

        return self

    def __eq__(self, other):
        if other.__model_name__ != self.__model_name__:
            # has to be of the same model
            return False
        if self.id and (other.id != self.id):
            # If the record has an ID the other one should
            # have the same.
            return False
        if not self.id and (self._values != other._values):
            # Unsaved records are same only if _values
            # of both are the same.
            return False
        return True


class ShopQuery(Query):
    """
    Implement web specific methods before starting to use query
    """
    def get_or_404(self, ident):
        """Like :meth:`get` but aborts with 404 if not found instead of returning ``None``."""

        rv = self.get(ident)
        if rv is None:
            abort(404)
        return rv

    def first_or_404(self):
        """Like :meth:`first` but aborts with 404 if not found instead of returning ``None``."""

        rv = self.first()
        if rv is None:
            abort(404)
        return rv

    def paginate(self, page=None, per_page=None, error_out=True):
        """Returns ``per_page`` items from page ``page``.
        If no items are found and ``page`` is greater than 1, or if page is less than 1, it aborts with 404.
        This behavior can be disabled by passing ``error_out=False``.
        If ``page`` or ``per_page`` are ``None``, they will be retrieved from the request query.
        If the values are not ints and ``error_out`` is ``True``, it aborts with 404.
        If there is no request or they aren't in the query, they default to 1 and 20 respectively.
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
        """Iterates over the page numbers in the pagination.  The four
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
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
