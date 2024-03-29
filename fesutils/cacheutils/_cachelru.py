#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/1 下午7:30

  * :class:`LRI` - Least-recently inserted
  * :class:`LRU` - Least-recently used

Both caches are :class:`dict` subtypes, designed to be as
interchangeable as possible, to facilitate experimentation. A key
practice with performance enhancement with caching is ensuring that
the caching strategy is working. If the cache is constantly missing,
it is just adding more overhead and code complexity. The standard
statistics are:

  * ``hit_count`` - the number of times the queried key has been in
    the cache
  * ``miss_count`` - the number of times a key has been absent and/or
    fetched by the cache
  * ``soft_miss_count`` - the number of times a key has been absent,
    but a default has been provided by the caller, as with
    :meth:`dict.get` and :meth:`dict.setdefault`. Soft misses are a
    subset of misses, so this number is always less than or equal to
    ``miss_count``.

由boltons库的cacheutils改造
"""

from operator import attrgetter
from threading import RLock

__all__ = ("LRI", "LRU", "cachedmethod", "cached", "make_sentinel", "_MISSING", "_KWARG_MARK")

PREV, NEXT, KEY, VALUE = range(4)  # names for the link fields
DEFAULT_MAX_SIZE = 128


class Sentinel(object):
    """
    Sentinel
    """

    def __init__(self, name, var_name):
        self.name = name
        self.var_name = var_name

    def __repr__(self):
        if self.var_name:
            return self.var_name
        return '%s(%r)' % (self.__class__.__name__, self.name)

    def __reduce__(self):
        if self.var_name:
            return self.var_name
        else:
            return super().__reduce__()

    @staticmethod
    def __nonzero__():
        return False

    __bool__ = __nonzero__


def make_sentinel(name='_MISSING', var_name=None):
    """Creates and returns a new **instance** of a new class, suitable for
    usage as a "sentinel", a kind of singleton often used to indicate
    a value is missing when ``None`` is a valid input.

    Args:
        name (str): Name of the Sentinel
        var_name (str): Set this name to the name of the variable in
            its respective module enable pickleability.

    >>> make_sentinel(var_name='_MISSING')
    _MISSING

    The most common use cases here in boltons are as default values
    for optional function arguments, partly because of its
    less-confusing appearance in automatically generated
    documentation. Sentinels also function well as placeholders in queues
    and linked lists.

    .. note::

      By design, additional calls to ``make_sentinel`` with the same
      values will not produce equivalent objects.

      >>> make_sentinel('TEST') == make_sentinel('TEST')
      False
      >>> type(make_sentinel('TEST')) == type(make_sentinel('TEST'))
      False

    """

    return Sentinel(name, var_name)


_MISSING = make_sentinel(var_name='_MISSING')
_KWARG_MARK = make_sentinel(var_name='_KWARG_MARK')


# noinspection PyMissingOrEmptyDocstring
class LRI(dict):
    """The ``LRI`` implements the basic *Least Recently Inserted* strategy to
    caching. One could also think of this as a ``SizeLimitedDefaultDict``.

    *on_miss* is a callable that accepts the missing key (as opposed
    to :class:`collections.defaultdict`'s "default_factory", which
    accepts no arguments.) Also note that, like the :class:`LRI`,
    the ``LRI`` is instrumented with statistics tracking.

    >>> cap_cache = LRI(max_size=2)
    >>> cap_cache['a'], cap_cache['b'] = 'A', 'B'
    >>> from pprint import pprint as pp
    >>> pp(dict(cap_cache))
    {'a': 'A', 'b': 'B'}
    >>> [cap_cache['b'] for i in range(3)][0]
    'B'
    >>> cap_cache['c'] = 'C'
    >>> print(cap_cache.get('a'))
    None
    >>> cap_cache.hit_count, cap_cache.miss_count, cap_cache.soft_miss_count
    (3, 1, 1)
    """

    def __init__(self, max_size=DEFAULT_MAX_SIZE, values=None, on_miss=None):
        super().__init__()
        if max_size <= 0:
            raise ValueError('expected max_size > 0, not %r' % max_size)
        self.hit_count = self.miss_count = self.soft_miss_count = 0
        self.max_size = max_size
        self._lock = RLock()
        self._init_ll()

        if on_miss is not None and not callable(on_miss):
            raise TypeError('expected on_miss to be a callable'
                            ' (or None), not %r' % on_miss)
        self.on_miss = on_miss

        if values:
            self.update(values)

    # invariants:
    # 1) 'anchor' is the sentinel node in the doubly linked list.  there is
    #    always only one, and its KEY and VALUE are both _MISSING.
    # 2) the most recently accessed node comes immediately before 'anchor'.
    # 3) the least recently accessed node comes immediately after 'anchor'.
    def _init_ll(self):
        anchor = []
        anchor[:] = [anchor, anchor, _MISSING, _MISSING]
        # a link lookup table for finding linked list links in O(1)
        # time.
        self._link_lookup = {}
        self._anchor = anchor

    def _get_flattened_ll(self):
        flattened_list = []
        link = self._anchor
        while True:
            flattened_list.append((link[KEY], link[VALUE]))
            link = link[NEXT]
            if link is self._anchor:
                break
        return flattened_list

    def _get_link_and_move_to_front_of_ll(self, key):
        # find what will become the newest link. this may raise a
        # KeyError, which is useful to __getitem__ and __setitem__
        newest = self._link_lookup[key]

        # splice out what will become the newest link.
        newest[PREV][NEXT] = newest[NEXT]
        newest[NEXT][PREV] = newest[PREV]

        # move what will become the newest link immediately before
        # anchor (invariant 2)
        anchor = self._anchor
        second_newest = anchor[PREV]
        second_newest[NEXT] = anchor[PREV] = newest
        newest[PREV] = second_newest
        newest[NEXT] = anchor
        return newest

    def _set_key_and_add_to_front_of_ll(self, key, value):
        # create a new link and place it immediately before anchor
        # (invariant 2).
        anchor = self._anchor
        second_newest = anchor[PREV]
        newest = [second_newest, anchor, key, value]
        second_newest[NEXT] = anchor[PREV] = newest
        self._link_lookup[key] = newest

    def _set_key_and_evict_last_in_ll(self, key, value):
        # the link after anchor is the oldest in the linked list
        # (invariant 3).  the current anchor becomes a link that holds
        # the newest key, and the oldest link becomes the new anchor
        # (invariant 1).  now the newest link comes before anchor
        # (invariant 2).  no links are moved; only their keys
        # and values are changed.
        oldanchor = self._anchor
        oldanchor[KEY] = key
        oldanchor[VALUE] = value

        self._anchor = anchor = oldanchor[NEXT]
        evicted = anchor[KEY]
        anchor[KEY] = anchor[VALUE] = _MISSING
        del self._link_lookup[evicted]
        self._link_lookup[key] = oldanchor
        return evicted

    def _remove_from_ll(self, key):
        # splice a link out of the list and drop it from our lookup
        # table.
        link = self._link_lookup.pop(key)
        link[PREV][NEXT] = link[NEXT]
        link[NEXT][PREV] = link[PREV]

    def __setitem__(self, key, value):
        with self._lock:
            try:
                link = self._get_link_and_move_to_front_of_ll(key)
            except KeyError:
                if len(self) < self.max_size:
                    self._set_key_and_add_to_front_of_ll(key, value)
                else:
                    evicted = self._set_key_and_evict_last_in_ll(key, value)
                    super(LRI, self).__delitem__(evicted)
                super(LRI, self).__setitem__(key, value)
            else:
                link[VALUE] = value

    def __getitem__(self, key):
        with self._lock:
            try:
                link = self._link_lookup[key]
            except KeyError:
                self.miss_count += 1
                if not self.on_miss:
                    raise
                ret = self[key] = self.on_miss(key)
                return ret

            self.hit_count += 1
            return link[VALUE]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self.soft_miss_count += 1
            return default

    def __delitem__(self, key):
        with self._lock:
            super(LRI, self).__delitem__(key)
            self._remove_from_ll(key)

    def pop(self, key, default=_MISSING):
        # NB: hit/miss counts are bypassed for pop()
        with self._lock:
            try:
                ret = super(LRI, self).pop(key)
            except KeyError:
                if default is _MISSING:
                    raise
                ret = default
            else:
                self._remove_from_ll(key)
            return ret

    def popitem(self):
        with self._lock:
            item = super(LRI, self).popitem()
            self._remove_from_ll(item[0])
            return item

    def clear(self):
        with self._lock:
            super(LRI, self).clear()
            self._init_ll()

    def copy(self):
        return self.__class__(max_size=self.max_size, values=self)

    def setdefault(self, key, default=None):
        with self._lock:
            try:
                return self[key]
            except KeyError:
                self.soft_miss_count += 1
                self[key] = default
                return default

    def update(self, E, **F):
        # E and F are throwback names to the dict() __doc__
        with self._lock:
            if E is self:
                return
            setitem = self.__setitem__
            if callable(getattr(E, 'keys', None)):
                for k in E.keys():
                    setitem(k, E[k])
            else:
                for k, v in E:
                    setitem(k, v)
            for k in F:
                setitem(k, F[k])
            return

    def __eq__(self, other):
        with self._lock:
            if self is other:
                return True
            if len(other) != len(self):
                return False
            if not isinstance(other, LRI):
                return other == self
            return super(LRI, self).__eq__(other)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        cn = self.__class__.__name__
        val_map = super(LRI, self).__repr__()
        return ('%s(max_size=%r, on_miss=%r, values=%s)'
                % (cn, self.max_size, self.on_miss, val_map))


# noinspection PyUnresolvedReferences
class LRU(LRI):
    """The ``LRU`` is :class:`dict` subtype implementation of the
    *Least-Recently Used* caching strategy.

    Args:
        max_size (int): Max number of items to cache. Defaults to ``128``.
        values (iterable): Initial values for the cache. Defaults to ``None``.
        on_miss (callable): a callable which accepts a single argument, the
            key not present in the cache, and returns the value to be cached.

    >>> cap_cache = LRU(max_size=2)
    >>> cap_cache['a'], cap_cache['b'] = 'A', 'B'
    >>> from pprint import pprint as pp
    >>> pp(dict(cap_cache))
    {'a': 'A', 'b': 'B'}
    >>> [cap_cache['b'] for i in range(3)][0]
    'B'
    >>> cap_cache['c'] = 'C'
    >>> print(cap_cache.get('a'))
    None

    This cache is also instrumented with statistics
    collection. ``hit_count``, ``miss_count``, and ``soft_miss_count``
    are all integer members that can be used to introspect the
    performance of the cache. ("Soft" misses are misses that did not
    raise :exc:`KeyError`, e.g., ``LRU.get()`` or ``on_miss`` was used to
    cache a default.

    >>> cap_cache.hit_count, cap_cache.miss_count, cap_cache.soft_miss_count
    (3, 1, 1)

    Other than the size-limiting caching behavior and statistics,
    ``LRU`` acts like its parent class, the built-in Python :class:`dict`.
    """

    def __getitem__(self, key):
        with self._lock:
            try:
                link = self._get_link_and_move_to_front_of_ll(key)
            except KeyError:
                self.miss_count += 1
                if not self.on_miss:
                    raise
                ret = self[key] = self.on_miss(key)
                return ret

            self.hit_count += 1
            return link[VALUE]


# Cached decorator
# Key-making technique adapted from Python 3.4's functools
class _HashedKey(list):
    """The _HashedKey guarantees that hash() will be called no more than once
    per cached function invocation.
    """
    __slots__ = 'hash_value'

    def __init__(self, key):
        super().__init__()
        self[:] = key
        self.hash_value = hash(tuple(key))

    def __hash__(self):
        return self.hash_value

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, list.__repr__(self))


# noinspection PyRedundantParentheses
def make_cache_key(args, kwargs, typed=False,
                   kwarg_mark=_KWARG_MARK,
                   fasttypes=frozenset([int, str, frozenset, type(None)])):
    """Make a generic key from a function's positional and keyword
    arguments, suitable for use in caches. Arguments within *args* and
    *kwargs* must be `hashable`_. If *typed* is ``True``, ``3`` and
    ``3.0`` will be treated as separate keys.

    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.

    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.

    >>> tuple(make_cache_key(('a', 'b'), {'c': ('d')}))
    ('a', 'b', _KWARG_MARK, ('c', 'd'))

    """

    # key = [func_name] if func_name else []
    # key.extend(args)
    key = list(args)
    sorted_items = {}.items()
    if kwargs:
        sorted_items = sorted(kwargs.items())
        key.append(kwarg_mark)
        key.extend(sorted_items)
    if typed:
        key.extend([type(v) for v in args])
        if kwargs:
            key.extend([type(v) for k, v in sorted_items])
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedKey(key)


# for backwards compatibility in case someone was importing it
_make_cache_key = make_cache_key


class CachedFunction(object):
    """This type is used by :func:`cached`, below. Instances of this
    class are used to wrap functions in caching logic.
    """

    def __init__(self, func, cache, scoped=True, typed=False, key=None):
        self.func = func
        if callable(cache):
            self.get_cache = cache
        elif not (callable(getattr(cache, '__getitem__', None))
                  and callable(getattr(cache, '__setitem__', None))):
            raise TypeError('expected cache to be a dict-like object,'
                            ' or callable returning a dict-like object, not %r'
                            % cache)
        else:
            def _get_cache():
                return cache

            self.get_cache = _get_cache
        self.scoped = scoped
        self.typed = typed
        self.key_func = key or make_cache_key

    def __call__(self, *args, **kwargs):
        cache = self.get_cache()
        key = self.key_func(args, kwargs, typed=self.typed)
        try:
            ret = cache[key]
        except KeyError:
            ret = cache[key] = self.func(*args, **kwargs)
        return ret

    def __repr__(self):
        cn = self.__class__.__name__
        if self.typed or not self.scoped:
            return ("%s(func=%r, scoped=%r, typed=%r)"
                    % (cn, self.func, self.scoped, self.typed))
        return "%s(func=%r)" % (cn, self.func)


class CachedMethod(object):
    """Similar to :class:`CachedFunction`, this type is used by
    :func:`cachedmethod` to wrap methods in caching logic.
    """

    def __init__(self, func, cache, scoped=True, typed=False, key=None):
        self.func = func
        self.__isabstractmethod__ = getattr(func, '__isabstractmethod__', False)
        if isinstance(cache, (str, bytes)):
            self.get_cache = attrgetter(cache)
        elif callable(cache):
            self.get_cache = cache
        elif not (callable(getattr(cache, '__getitem__', None))
                  and callable(getattr(cache, '__setitem__', None))):
            raise TypeError('expected cache to be an attribute name,'
                            ' dict-like object, or callable returning'
                            ' a dict-like object, not %r' % cache)
        else:
            # noinspection PyUnusedLocal
            def _get_cache(obj):
                return cache

            self.get_cache = _get_cache
        self.scoped = scoped
        self.typed = typed
        self.key_func = key or make_cache_key
        self.bound_to = None

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        cls = self.__class__
        ret = cls(self.func, self.get_cache, typed=self.typed,
                  scoped=self.scoped, key=self.key_func)
        ret.bound_to = obj
        return ret

    def __call__(self, *args, **kwargs):
        obj = args[0] if self.bound_to is None else self.bound_to
        cache = self.get_cache(obj)
        key_args = (self.bound_to, self.func) + args if self.scoped else args
        key = self.key_func(key_args, kwargs, typed=self.typed)
        try:
            ret = cache[key]
        except KeyError:
            if self.bound_to is not None:
                args = (self.bound_to,) + args
            ret = cache[key] = self.func(*args, **kwargs)
        return ret

    # noinspection PyStringFormat
    def __repr__(self):
        cn = self.__class__.__name__
        args = (cn, self.func, self.scoped, self.typed)
        if self.bound_to is not None:
            args += (self.bound_to,)
            return '<%s func=%r scoped=%r typed=%r bound_to=%r>' % args
        return "%s(func=%r, scoped=%r, typed=%r)" % args


# noinspection PyUnresolvedReferences
def cached(cache, scoped=True, typed=False, key=None):
    """Cache any function with the cache object of your choosing. Note
    that the function wrapped should take only `hashable`_ arguments.

    Args:
        cache (Mapping): Any :class:`dict`-like object suitable for
            use as a cache. Instances of the :class:`LRU` and
            :class:`LRI` are good choices, but a plain :class:`dict`
            can work in some cases, as well. This argument can also be
            a callable which accepts no arguments and returns a mapping.
        scoped (bool): Whether the function itself is part of the
            cache key.  ``True`` by default, different functions will
            not read one another's cache entries, but can evict one
            another's results. ``False`` can be useful for certain
            shared cache use cases. More advanced behavior can be
            produced through the *key* argument.
        typed (bool): Whether to factor argument types into the cache
            check. Default ``False``, setting to ``True`` causes the
            cache keys for ``3`` and ``3.0`` to be considered unequal.
        key:

    >>> my_cache = LRU()
    >>> @cached(my_cache)
    ... def cached_lower(x):
    ...     return x.lower()
    ...
    >>> cached_lower("CaChInG's FuN AgAiN!")
    "caching's fun again!"
    >>> len(my_cache)
    1

    """

    # noinspection PyMissingOrEmptyDocstring
    def cached_func_decorator(func):
        return CachedFunction(func, cache, scoped=scoped, typed=typed, key=key)

    return cached_func_decorator


# noinspection PyUnresolvedReferences
def cachedmethod(cache, scoped=True, typed=False, key=None):
    """Similar to :func:`cached`, ``cachedmethod`` is used to cache
    methods based on their arguments, using any :class:`dict`-like
    *cache* object.

    Args:
        cache (str/Mapping/callable): Can be the name of an attribute
            on the instance, any Mapping/:class:`dict`-like object, or
            a callable which returns a Mapping.
        scoped (bool): Whether the method itself and the object it is
            bound to are part of the cache keys. ``True`` by default,
            different methods will not read one another's cache
            results. ``False`` can be useful for certain shared cache
            use cases. More advanced behavior can be produced through
            the *key* arguments.
        typed (bool): Whether to factor argument types into the cache
            check. Default ``False``, setting to ``True`` causes the
            cache keys for ``3`` and ``3.0`` to be considered unequal.
        key (callable): A callable with a signature that matches
            :func:`make_cache_key` that returns a tuple of hashable
            values to be used as the key in the cache.

    >>> class Lowerer(object):
    ...     def __init__(self):
    ...         self.cache = LRI()
    ...
    ...     @cachedmethod('cache')
    ...     def lower(self, text):
    ...         return text.lower()
    ...
    >>> lowerer = Lowerer()
    >>> lowerer.lower('WOW WHO COULD GUESS CACHING COULD BE SO NEAT')
    'wow who could guess caching could be so neat'
    >>> len(lowerer.cache)
    1

    """

    # noinspection PyMissingOrEmptyDocstring
    def cached_method_decorator(func):
        return CachedMethod(func, cache, scoped=scoped, typed=typed, key=key)

    return cached_method_decorator
