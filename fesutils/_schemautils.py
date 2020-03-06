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
from typing import Callable, Dict, List, Tuple, Union

import aelog
from marshmallow import EXCLUDE, Schema, ValidationError, fields

from fesutils._err_msg import schema_msg
from fesutils.err import FuncArgsError, HttpError

__all__ = ("schema_validated", "schema_validate", "schema2swagger")


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
                     excluded: Union[Tuple, List] = tuple(), message: Dict = None, is_async: bool = True) -> Callable:
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
            if excluded:
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


def schema2swagger(cls_schema: Schema, excluded: Union[Tuple, List] = tuple(),
                   require_only: Union[Tuple, List] = tuple()):
    """
    转换schema为swagger的dict，这样就减少书写swagger文档的麻烦
    Args:
        cls_schema: schema class
        excluded: 排除那些字段不需要展示
        require_only: 仅需要展示的字段
    Returns:
        返回swagger json body doc.JsonBody
    """
    try:
        from sanic_openapi import doc
    except ImportError as e:
        raise ImportError(f"please pip install Sanic {e}")

    schema_swagger_map = {
        fields.Email.__name__: doc.String,
        fields.String.__name__: doc.String,
        fields.Integer.__name__: doc.Integer,
        fields.Url.__name__: doc.String,
        fields.Boolean.__name__: doc.Boolean,
        fields.Float.__name__: doc.Float,
        fields.DateTime.__name__: doc.DateTime,
        fields.UUID.__name__: doc.String,
        fields.Number.__name__: doc.Float,
        fields.Raw.__name__: doc.String  # 暂时没有合适的去表示这个映射
    }

    if not isinstance(require_only, (tuple, list)):
        raise FuncArgsError(message="require_only type error!")
    if not isinstance(excluded, (tuple, list)):
        raise FuncArgsError(message="excluded type error!")

    def iter_schema(sub_cls_schema, iter_once=False):
        """
        递归处理每个迭代子集
        Args:
            sub_cls_schema: schema class
            iter_once: 控制是否迭代一次，对于包含自身的嵌套来说是有用的
        Returns:
            返回 dictionary
        """
        swagger_dict = {}
        if not issubclass(sub_cls_schema, Schema):
            raise FuncArgsError("cls_schema must be sub clss of Schema.")
        for key, obj in getattr(sub_cls_schema, "_declared_fields", {}).items():
            if require_only and key not in require_only:  # require_only 和 excluded互斥
                continue
            elif key in ("created_time", "updated_time", *excluded):  # 过滤掉时间字段
                continue
            if isinstance(obj, fields.Field):
                obj_name = obj.__class__.__name__
                obj_required = getattr(obj, "required", None)
                verbose_name = getattr(obj, "metadata").get("verbose_name", "")
                if obj_name in schema_swagger_map:  # 处理普通schema
                    swagger_dict[key] = schema_swagger_map[obj_name](verbose_name, required=obj_required)
                elif obj_name == "List":  # 处理列表
                    swagger_dict[key] = handle_list(obj, obj_required, verbose_name)
                elif obj_name == "Dict":
                    swagger_dict[key] = handle_dict(obj, obj_required, verbose_name)
                elif obj_name == "Nested":  # 递归处理嵌套schema
                    if getattr(obj, "nested") == "self":  # 处理schema包含自身的情况, 包含自身的情况只递归处理一次
                        if not iter_once:
                            swagger_dict[key] = iter_schema(sub_cls_schema, True)
                    else:
                        sub_cls_schema = getattr(obj, "nested")
                        swagger_dict[key] = iter_schema(sub_cls_schema)
        return swagger_dict

    def handle_list(obj, obj_required, verbose_name):
        """
        递归处理每个迭代子集
        Args:
            obj: 最外层循环的object对象
            obj_required: 最外层对象require参数值
            verbose_name: 最外层的名称
        Returns:

        """
        sub_obj = getattr(obj, "container", None)
        sub_obj_name = sub_obj.__class__.__name__
        sub_verbose_name = getattr(sub_obj, "metadata").get("verbose_name", "")
        sub_obj_required = getattr(sub_obj, "required", None)
        if sub_obj_name == "Nested":  # 递归处理嵌套schema,处理list中包含嵌套的schema情况
            sub_cls_schema = getattr(sub_obj, "nested")  # 暂时没有遇到列表中会嵌套自身的情况，不做处理
            return doc.List(iter_schema(sub_cls_schema), required=obj_required, description=verbose_name)
        elif sub_obj_name == "Dict":
            value_obj = handle_dict(sub_obj, sub_obj_required, sub_verbose_name)
            return doc.List(value_obj, required=obj_required, description=verbose_name)
        else:
            return doc.List(schema_swagger_map[sub_obj_name](sub_verbose_name, required=sub_obj_required),
                            required=obj_required, description=verbose_name)

    def handle_dict(obj, obj_required, verbose_name):
        """
        递归处理每个迭代子集
        Args:
            obj: 最外层循环的object对象
            obj_required: 最外层对象require参数值
            verbose_name: 最外层的名称
        Returns:

        """
        key_obj, value_obj = getattr(obj, "key_container", None), getattr(obj, "value_container", None)
        key_name, value_name = key_obj.__class__.__name__, value_obj.__class__.__name__
        key_required, value_required = getattr(key_obj, "required", None), getattr(key_obj, "required", None)
        # 个别情况下会存在MySQL存储的json,而这时候不需要对json内部的结构进行预估
        if key_required and value_required:
            key_verbose_name = getattr(key_obj, "metadata").get("verbose_name", "")
            value_verbose_name = getattr(value_obj, "metadata").get("verbose_name", "")
            key_obj = schema_swagger_map[key_name](key_verbose_name, required=key_required)
            if value_name == "Nested":
                dict_cls_schema = getattr(value_obj, "nested")
                value_obj = iter_schema(dict_cls_schema)
            elif value_name == "Dict":
                value_obj = handle_dict(value_obj, value_required, value_verbose_name)
            elif value_name == "List":
                value_obj = handle_list(value_obj, value_required, value_verbose_name)
            else:
                value_obj = schema_swagger_map[value_name](value_verbose_name, required=value_required)
            return doc.Dictionary({"key": key_obj, "value": value_obj}, description=verbose_name, required=obj_required)
        else:
            return doc.Dictionary(description=verbose_name, required=obj_required)

    result = iter_schema(cls_schema)
    return doc.JsonBody(result)
