#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 19-1-21 下午6:47

schema校验，需要安装flask或者sanic
"""
from collections import MutableMapping, MutableSequence
from functools import partial, wraps
from typing import Dict, List, Tuple, Union

import aelog
from marshmallow import EXCLUDE, Schema, ValidationError

from fesutils._err_msg import schema_msg
from fesutils.err import FuncArgsError, HttpError

__all__ = ("schema_validated", "schema_validate")


def _verify_message(src_message: Dict, message: Union[List, Dict]):
    """
    对用户提供的message进行校验
    Args:
        src_message: 默认提供的消息内容
        message: 指定的消息内容
    Returns:

    """
    src_message = dict(src_message)
    message = message if isinstance(message, MutableSequence) else [message]
    required_field = {"msg_code", "msg_zh", "msg_en"}

    for msg in message:
        if isinstance(msg, MutableMapping):
            if set(msg.keys()).intersection(required_field) == required_field and msg["msg_code"] in src_message:
                src_message[msg["msg_code"]].update(msg)
    return src_message


def schema_validated(schema_obj, required: Union[Tuple, List] = tuple(), is_extends: bool = True,
                     excluded: Union[Tuple, List] = tuple(), message: Dict = None, is_async: bool = True):
    """
    校验post的json格式和类型是否正确
    Args:
        schema_obj: 定义的schema对象
        required: 需要标记require的字段
        excluded: 排除不需要的字段
        is_extends: 是否继承schemea本身其他字段的require属性， 默认继承
        message: 提示消息
        is_async: 是否异步库,用于区分sanic和flask,默认sanic异步框架
    Returns:
    """
    if is_async is True:
        try:
            from sanic.request import Request
        except ImportError as e:
            raise ImportError(f"please pip install Sanic {e}")
    else:
        try:
            from flask import g, request
        except ImportError as e:
            raise ImportError(f"please pip install Sanic {e}")

    if not issubclass(schema_obj, Schema):
        raise FuncArgsError(message="schema_obj type error!")
    if not isinstance(required, (tuple, list)):
        raise FuncArgsError(message="required type error!")
    if not isinstance(excluded, (tuple, list)):
        raise FuncArgsError(message="excluded type error!")

    # 此处的功能保证，如果调用了多个校验装饰器，则其中一个更改了，所有的都会更改
    if not getattr(schema_validated, "message", None):
        setattr(schema_validated, "message", _verify_message(schema_msg, message or {}))

    def _verify_schema(request_, schema_message):
        schema_obj_ = schema_obj(unknown=EXCLUDE)
        if required:
            for key, val in schema_obj_.fields.items():
                if key in required:  # 反序列化期间，把特别需要的字段标记为required
                    setattr(schema_obj_.fields[key], "required", True)
                    setattr(schema_obj_.fields[key], "dump_only", False)
                elif not is_extends:
                    setattr(schema_obj_.fields[key], "required", False)
        try:
            valid_data = schema_obj_.load(request_.json, unknown=EXCLUDE)
            # 把load后不需要的字段过滤掉，主要用于不允许修改的字段load后过滤掉
            for val in excluded:
                valid_data.pop(val, None)
        except ValidationError as err:
            # 异常退出
            aelog.exception('Request body validation error, please check! {} {} error={}'.format(
                request_.method, request_.path, err.messages))
            raise HttpError(400, message=schema_message[201]["msg_zh"], error=err.messages)
        except Exception as err:
            aelog.exception("Request body validation unknow error, please check!. {} {} error={}".format(
                request_.method, request_.path, str(err)))
            raise HttpError(500, message=schema_message[202]["msg_zh"], error=str(err))
        else:
            return valid_data

    def _validated(func):
        """
        校验post的json格式和类型是否正确
        """

        @wraps(func)
        async def _async_wrapper(*args, **kwargs):
            """
            校验post的json格式和类型是否正确
            """
            schema_message = getattr(schema_validated, "message", None)
            request_ = args[0] if isinstance(args[0], Request) else args[1]

            request_["json"] = _verify_schema(request_, schema_message)
            return await func(*args, **kwargs)

        @wraps(func)
        def _wrapper(*args, **kwargs):
            """
            校验post的json格式和类型是否正确
            """
            schema_message = getattr(schema_validated, "message", None)

            g.json = _verify_schema(request, schema_message)
            return func(*args, **kwargs)

        return _async_wrapper if is_async is True else _wrapper

    return _validated


# 用于flask框架中的schema校验
schema_validate = partial(schema_validated, is_async=False)
