#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午6:29
"""

import weakref

__all__ = ("Singleton", "Cached")


class _Singleton(type):
    """
    singleton for class
    """

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance
        else:
            return cls.__instance


class _Cached(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.__cache = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        cached_name = f"{args}{kwargs}"
        if cached_name in cls.__cache:
            return cls.__cache[cached_name]
        else:
            obj = super().__call__(*args, **kwargs)
            cls.__cache[cached_name] = obj  # 这里是弱引用不能直接赋值，否则会被垃圾回收期回收
            return obj


class Singleton(metaclass=_Singleton):
    pass


class Cached(metaclass=_Cached):
    pass
