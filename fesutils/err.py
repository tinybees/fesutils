#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-25 下午2:08
"""

__all__ = ("Error", "EmailError", "ConfigError", "FuncArgsError", "QueryArgsError", "CommandArgsError",
           "InvalidId", "HttpError")


class Error(Exception):
    """
    异常基类
    """

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return "Error: message='{}'".format(self.message)

    def __repr__(self):
        return "<{} '{}'>".format(self.__class__.__name__, self.message)


class HttpError(Error):
    """
    主要处理http 错误,从接口返回
    """

    def __init__(self, status_code, *, message=None, error=None):
        self.status_code = status_code
        self.message = message
        self.error = error

    def __str__(self):
        return "{}, '{}':'{}'".format(self.status_code, self.message, self.message or self.error)

    def __repr__(self):
        return "<{} '{}: {}'>".format(self.__class__.__name__, self.status_code, self.error or self.message)


class EmailError(Error):
    """
    主要处理email error
    """

    pass


class ConfigError(Error):
    """
    主要处理config error
    """

    pass


class FuncArgsError(Error):
    """
    处理函数参数不匹配引发的error
    """

    pass


class QueryArgsError(Error):
    """
    处理salalemy 拼接query错误
    """

    pass


class CommandArgsError(Error):
    """
    处理执行命令时，命令失败错误
    """

    pass


class InvalidId(Error):
    """Raised when trying to create an ObjectId from invalid data.
    """
