#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-26 下午3:32

包装工具类
"""

import asyncio
from contextlib import contextmanager
from functools import wraps

from .err import Error, FuncArgsError

__all__ = ("ignore_error", "wrap_async_func", "singleton")


def singleton(cls):
    """
    singleton for class
    """

    instances = {}

    @wraps(cls)
    def _singleton(*args, **kwargs):
        """
        singleton for class of app
        """
        cls_name = "_{0}".format(cls)
        if cls_name not in instances:
            instances[cls_name] = cls(*args, **kwargs)
        return instances[cls_name]

    return _singleton


@contextmanager
def ignore_error(error=Exception):
    """
    个别情况下会忽略遇到的错误
    Args:

    Returns:

    """
    # noinspection PyBroadException
    try:
        yield
    except error:
        pass


async def wrap_async_func(func, *args, **kwargs):
    """
    包装同步阻塞请求为异步非阻塞
    Args:
        func: 实际请求的函数名或者方法名
        args: 函数参数
        kwargs: 函数参数
    Returns:
        返回执行后的结果
    """
    try:
        result = await asyncio.wrap_future(pool.submit(func, *args, **kwargs))
    except TypeError as e:
        raise FuncArgsError("Args error: {}".format(e))
    except Exception as e:
        raise Error("Error: {}".format(e))
    else:
        return result
