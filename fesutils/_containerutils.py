#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2021/6/4 下午2:08

和容器相关的常用工具方法
"""
import itertools
from typing import Any, Callable, List, Tuple, Union

__all__ = ("expand_nested_list", "is_iterable", "chunked", "chunked_iter",)


def expand_nested_list(nested_list: Union[List, Tuple, None]):
    """
    多层嵌套的列表展开为一层
    Args:

    Returns:

    """
    if isinstance(nested_list, (list, tuple)):
        for one_result in nested_list:
            if isinstance(one_result, (list, tuple)):
                for one_result_ in expand_nested_list(one_result):
                    yield one_result_
            else:
                yield one_result


def is_iterable(obj):
    """Similar in nature to :func:`callable`, ``is_iterable`` returns
    ``True`` if an object is `iterable`_, ``False`` if not.

    >>> is_iterable([])
    True
    >>> is_iterable(object())
    False

    .. _iterable: https://docs.python.org/2/glossary.html#term-iterable
    """
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def chunked(src, size, count=None, **kw):
    """Returns a list of *count* chunks, each with *size* elements,
    generated from iterable *src*. If *src* is not evenly divisible by
    *size*, the final chunk will have fewer than *size* elements.
    Provide the *fill* keyword argument to provide a pad value and
    enable padding, otherwise no padding will take place.

    >>> chunked(range(10), 3)
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    >>> chunked(range(10), 3, fill=None)
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
    >>> chunked(range(10), 3, count=2)
    [[0, 1, 2], [3, 4, 5]]

    See :func:`chunked_iter` for more info.
    """
    chunk_iter = chunked_iter(src, size, **kw)
    if count is None:
        return list(chunk_iter)
    else:
        return list(itertools.islice(chunk_iter, count))


def chunked_iter(src, size, **kw):
    """Generates *size*-sized chunks from *src* iterable. Unless the
    optional *fill* keyword argument is provided, iterables not evenly
    divisible by *size* will have a final chunk that is smaller than
    *size*.

    >>> list(chunked_iter(range(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    >>> list(chunked_iter(range(10), 3, fill=None))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]

    Note that ``fill=None`` in fact uses ``None`` as the fill value.
    """
    # TODO: add count kwarg?
    if not is_iterable(src):
        raise TypeError('expected an iterable')
    size = int(size)
    if size <= 0:
        raise ValueError('expected a positive integer chunk size')
    do_fill = True
    try:
        fill_val = kw.pop('fill')
    except KeyError:
        do_fill = False
        fill_val = None
    if kw:
        raise ValueError('got unexpected keyword arguments: %r' % kw.keys())
    if not src:
        return
    postprocess: Callable[[Any], Any] = lambda chk: chk
    if isinstance(src, (str, bytes)):
        postprocess = lambda chk, _sep=type(src)(): _sep.join(chk)
        if isinstance(src, bytes):
            postprocess = lambda chk: bytes(chk)
    src_iter = iter(src)
    while True:
        cur_chunk = list(itertools.islice(src_iter, size))
        if not cur_chunk:
            break
        lc = len(cur_chunk)
        if lc < size and do_fill:
            cur_chunk[lc:] = [fill_val] * (size - lc)
        yield postprocess(cur_chunk)
    return
