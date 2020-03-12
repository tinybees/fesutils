#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/9 下午8:00
"""
import sys
from datetime import datetime
from time import localtime, mktime
from typing import Union

from marshmallow.utils import from_iso_datetime

__all__ = ("gmt2time", "ymd2time", "time2gmt", "time2ymd", "iso2time", "time2iso", "stamp2time", "time2stamp")


def time2gmt(dt_val: Union[datetime, int, float, None] = None, delim=' ') -> str:
    """
    datetime时间格式化为GMT时间字符串
    Args:
        dt_val: 时间值类型为datetime,int,float
        delim: 间隔字符串
    Returns:
        eg； Thu, 12 Mar 2020 11:21:04 GMT
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


def time2ymd(dt_val: Union[datetime, int, float, None] = None) -> str:
    """
    datetime时间格式化为Y-M-D的格式
    Args:
        dt_val: Union[datetime, int, float, None] = None, delim=' '
    Returns:
        eg: 2020-03-12 11:21:04
    """
    if dt_val is None:
        dt_val = localtime()
    elif isinstance(dt_val, datetime):
        dt_val = dt_val.timetuple()
    elif isinstance(dt_val, (int, float)):
        dt_val = localtime(dt_val)

    return '%s-%02d-%02d %02d:%02d:%02d' % (
        str(dt_val.tm_year), dt_val.tm_mon, dt_val.tm_mday, dt_val.tm_hour, dt_val.tm_min, dt_val.tm_sec)


def time2iso(dt_val: Union[datetime, int, float, None] = None) -> str:
    """
    datetime时间格式化为ISO时间字符串
    Args:
       dt_val: 时间值类型为datetime,int,float
    Returns:
        eg :2020-03-12T11:49:31.392460
    """
    if dt_val is None:
        dt_val = datetime.now()
    elif isinstance(dt_val, (int, float)):
        dt_val = localtime(dt_val)
        dt_val = datetime.fromtimestamp(mktime(dt_val))
    return dt_val.isoformat()


def time2stamp(dt_val: Union[datetime, int, float, None] = None, length=13) -> int:
    """
    datetime时间格式化为timestamp 13位时间戳
    Args:
       dt_val: 时间值类型为datetime,int,float
       length: 时间戳长度
    Returns:
        eg :1583985504763
    """
    if dt_val is None:
        dt_val = datetime.now()
    elif isinstance(dt_val, (int, float)):
        dt_val = localtime(dt_val)
        dt_val = datetime.fromtimestamp(mktime(dt_val))
    return int(dt_val.timestamp() * 1000) if length == 13 else int(dt_val.timestamp())


def gmt2time(gmt_val: str) -> datetime:
    """
    解析GMT字符串时间到datetime类型
    Args:
        gmt_val: gmt时间字符串, eg: Thu, 12 Mar 2020 11:21:04 GMT
    Returns:
        datetime
    """
    return datetime.strptime(gmt_val, '%a, %d %b %Y %H:%M:%S GMT')


def ymd2time(ymd_val: str) -> datetime:
    """
    解析年月日字符串时间到datetime类型
    Args:
        ymd_val: 年月日时间字符串, eg: 2020-03-12 11:21:04
    Returns:
        datetime
    """
    return datetime.strptime(ymd_val, '%Y-%m-%d %H:%M:%S')


def iso2time(iso_val: str) -> datetime:
    """
    解析iso字符串时间到datetime类型
    Args:
        iso_val: 年月日时间字符串, eg: 2020-03-12T11:49:31.392460
    Returns:
        datetime
    """
    if sys.version_info >= (3, 7):
        dt_val = datetime.fromisoformat(iso_val)
    else:
        dt_val = from_iso_datetime(iso_val)
    return dt_val


def stamp2time(stamp_val: Union[int, float, str]) -> datetime:
    """
    解析time stamp时间戳到datetime类型
    Args:
        stamp_val: 年月日时间字符串, eg: 1583985504763
    Returns:
        datetime
    """

    left, *right = str(stamp_val).split(".")
    right = "".join(right)
    left_, right_ = left[:10], left[10:]
    stamp_val = float(f"{left_}.{right_}{right}")
    return datetime.fromtimestamp(stamp_val)


if __name__ == '__main__':
    print(time2ymd(datetime.now()))
    print(time2gmt(datetime.now()))
    print(time2iso())
    print(iso2time("2020-03-12T11:49:31.392460"))
    print(time2stamp())
    print(stamp2time(1583986340707))
    print(stamp2time("1583986340707"))
    print(stamp2time(1583986340.707))
    print(stamp2time(1583986340707.111))
