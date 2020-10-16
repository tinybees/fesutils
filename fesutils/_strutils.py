#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午6:36
"""
import hashlib
import re
import secrets
import string
import uuid
from typing import Union

__all__ = ("gen_ident", "gen_unique_ident", "camel2under", "under2camel", "number", "str2md5")

_camel2under_re = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def gen_ident(ident_len: int = 8):
    """
    获取随机的标识码以字母开头， 默认8个字符的长度
    Args:

    Returns:

    """
    alphabet = f"{string.ascii_lowercase}{string.digits}"
    ident = ''.join(secrets.choice(alphabet) for _ in range(ident_len - 1))
    return f"{secrets.choice(string.ascii_lowercase)}{ident}"


def gen_unique_ident():
    """
    获取以字母开头的唯一字符串
    Args:

    Returns:

    """

    return f"{secrets.choice(string.ascii_lowercase)}{uuid.uuid4().hex}"


def camel2under(camel_string):
    """Converts a camelcased string to underscores. Useful for turning a
    class name into a function name.

    >>> camel2under('BasicParseTest')
    'basic_parse_test'
    """
    return _camel2under_re.sub(r'_\1', camel_string).lower()


def under2camel(under_string):
    """Converts an underscored string to camelcased. Useful for turning a
    function name into a class name.

    >>> under2camel('complex_tokenizer')
    'ComplexTokenizer'
    """
    return ''.join(w.capitalize() or '_' for w in under_string.split('_'))


def number(str_value: str, default: Union[int, float] = 0) -> Union[int, float]:
    """
    把字符串值转换为int或者float
    Args:
        str_value: 需要转换的字符串值
        default: 转换失败的默认值,默认值只能为Number类型,默认为0
    Returns:

    """
    default = default if isinstance(default, (int, float)) else 0
    if isinstance(str_value, str):
        number_value: Union[int, float] = default  # 先赋予默认值
        # 处理有符号的整数和小数
        if str_value.startswith(("-", "+")):
            if str_value[1:].isdecimal():
                number_value = int(str_value)
            elif str_value[1:].replace(".", "").isdecimal():
                number_value = float(str_value)
        # 处理无符号的整数
        elif str_value.isdecimal():
            number_value = int(str_value)
        # 处理无符号的小数
        elif str_value.replace(".", "").isdecimal():
            number_value = float(str_value)

        return number_value
    elif isinstance(str_value, (int, float)):
        return str_value
    else:
        return default


def str2md5(content: str):
    """
    获取内容的MD5值
    Args:
        content: str
    Returns:

    """
    h = hashlib.md5()
    h.update(content.encode())
    return h.hexdigest()
