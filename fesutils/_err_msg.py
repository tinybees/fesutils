#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-25 下午2:42
可配置消息模块
"""

__all__ = ("schema_msg",)

schema_msg = {
    # schema valication message
    201: {"msg_code": 201, "msg_zh": "数据提交有误，请重新检查.", "msg_en": "Request body validation error, please check!",
          "description": "marmallow校验body错误时的提示"},
    202: {"msg_code": 202, "msg_zh": "数据提交未知错误，请重新检查.",
          "msg_en": "Request body validation unknow error, please check!",
          "description": "marmallow校验body未知错误时的提示"},
}
