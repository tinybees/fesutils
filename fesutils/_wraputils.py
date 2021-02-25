#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-26 下午3:32

包装工具类
"""

import asyncio
import inspect
from collections import MutableMapping, Sequence
from contextlib import contextmanager
from functools import wraps

from aiocontext import async_contextmanager

from ._poolutils import pool
from .err import Error, FuncArgsError

__all__ = ("singleton", "ignore_error", "wrap_async_func", "wrap_async_funcs", "async_ignore_error")


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


@async_contextmanager
async def async_ignore_error(error=Exception):
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


async def wrap_async_funcs(funcs: list):
    """
    批量包装同步方法为异步，批量执行
    Args:
        funcs: 批量传入的参数列表,eg: [{"func":xx, "args":(), "kwargs":{}}, {"func":xx, "args":(), "kwargs":{}}]
    Returns:
        返回执行后的结果，顺序和传入的顺序一致
    """
    tasks = []
    for func in funcs:
        func = func.get("func")
        if not (inspect.isfunction(func) or inspect.ismethod(func)):
            raise FuncArgsError("Function type error, error: func={}".format(func))

        args = func.get("args")
        if args and not isinstance(args, Sequence):
            raise FuncArgsError("Args is not sequence type, func={}, args={}".format(func, args))
        else:
            args = ()

        kwargs = func.get("kwargs")
        if kwargs and not isinstance(kwargs, MutableMapping):
            raise FuncArgsError("Kwargs is not MutableMapping type, func={}, args={}".format(func, args))
        else:
            kwargs = {}

        tasks.append(asyncio.ensure_future(wrap_async_func(func, *args, **kwargs)))
    dones, _ = await asyncio.wait(tasks)
    return [task.result() for task in dones]
