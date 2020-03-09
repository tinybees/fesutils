#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/9 下午8:00
"""

from datetime import datetime
from time import localtime

__all__ = ("gmt2time", "ymd2time", "time2gmt", "time2ymd")

from typing import Union


def time2gmt(dt_val: Union[datetime, int, float, None] = None, delim=' '):
    """
    datetime时间格式化为GMT时间字符串
    Args:

    Returns:

    """
    if dt_val is None:
        dt_val = localtime()
    elif isinstance(dt_val, datetime):
        dt_val = dt_val.timetuple()
    elif isinstance(dt_val, (int, float)):
        dt_val = localtime(dt_val)
    return '%s, %02d%s%s%s%s %02d:%02d:%02d GMT' % (
        ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[dt_val.tm_wday],
        dt_val.tm_mday, delim,
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
         'Oct', 'Nov', 'Dec')[dt_val.tm_mon - 1],
        delim, str(dt_val.tm_year), dt_val.tm_hour, dt_val.tm_min, dt_val.tm_sec
    )


def time2ymd(dt_val: Union[datetime, int, float, None] = None):
    """
    datetime时间格式化为Y-M-D的格式
    Args:
        dt_val: Union[datetime, int, float, None] = None, delim=' '
    Returns:

    """
    if dt_val is None:
        dt_val = localtime()
    elif isinstance(dt_val, datetime):
        dt_val = dt_val.timetuple()
    elif isinstance(dt_val, (int, float)):
        dt_val = localtime(dt_val)

    return '%s-%02d-%02d %02d:%02d:%02d' % (
        str(dt_val.tm_year), dt_val.tm_mon, dt_val.tm_mday, dt_val.tm_hour, dt_val.tm_min, dt_val.tm_sec)


def gmt2time(gmt_str: str):
    """
    解析GMT字符串时间到datetime类型
    Args:

    Returns:

    """
    return datetime.strptime(gmt_str, '%a, %d %b %Y %H:%M:%S GMT')


def ymd2time(ymd_str: str):
    """
    解析年月日字符串时间到datetime类型
    Args:

    Returns:

    """
    return datetime.strptime(ymd_str, '%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    print(time2ymd(datetime.now()))
    print(time2gmt(datetime.now()))
