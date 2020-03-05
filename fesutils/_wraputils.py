#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-26 下午3:32

包装工具类
"""

import asyncio
import hashlib
import subprocess
from contextlib import contextmanager
from functools import wraps

import aelog

from ._poolutils import pool
from .err import CommandArgsError, Error, FuncArgsError

__all__ = ("ignore_error", "wrap_async_func", "singleton", "get_content_md5", "execute_shell", "async_execute_shell")


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


def get_content_md5(content: str):
    """
    获取内容的MD5值
    Args:
        content: str
    Returns:

    """
    h = hashlib.md5()
    h.update(content.encode())
    return h.hexdigest()


def execute_shell(name, cmd):
    """
    excute shell
    Args:
        name: 执行的命令名称
        cmd: 执行命令的实际内容
    Returns:

    """
    try:
        rs = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        aelog.exception("name={},code={}, msg={}".format(name, e.returncode, str(e.output)))
        raise CommandArgsError(f"{name} error, {str(e.output)}")
    else:
        return rs.decode(encoding="utf8")


async def async_execute_shell(cmd):
    """
    async excute shell
    Args:
        cmd: 要执行的命令字符串
    Returns:

    """
    process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    success_msg, error_msg = await process.stdout.read(), await process.stderr.read()
    returncode = await process.wait()
    if returncode == 0:
        return success_msg.decode()
    else:
        raise CommandArgsError(error_msg.decode())
