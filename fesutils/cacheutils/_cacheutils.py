#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午6:29
"""

import weakref
from collections import MutableMapping, UserDict
from typing import Dict
from weakref import WeakValueDictionary

__all__ = ("Singleton", "Cached", "UserConfig", "LocalCache", "g", "Config")


# noinspection Mypy
class _Singleton(type):
    """
    singleton for class
    """

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance
        else:
            return cls.__instance


# noinspection Mypy
class _Cached(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.__cache = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        cached_name = f"{args}{kwargs}"
        if cached_name in cls.__cache:
            return cls.__cache[cached_name]
        else:
            obj = super().__call__(*args, **kwargs)
            cls.__cache[cached_name] = obj  # 这里是弱引用不能直接赋值，否则会被垃圾回收期回收
            return obj


class Singleton(metaclass=_Singleton):
    """
    单例类
    """
    pass


class Cached(metaclass=_Cached):
    """
    枚举类
    """
    pass


class UserConfig(UserDict):
    """
    实际存储配置的地方
    """

    def __init__(self, dict_obj):
        """
            实际存储配置的地方
        Args:

        """
        super().__init__(dict_obj)

    def __getattr__(self, attr):
        """
            获取属性的值，如果属性存在则返回，否则返回None,减少报错次数
        Args:
            attr: 要获取的属性
        Returns:
            返回属性值或者None
        """
        return self.get(attr)


class LocalCache(UserDict):
    """
    主要用于项目启动后缓存各个枚举数据
    """

    def __init__(self, *args, **kwargs):
        """
            主要用于项目启动后缓存各个枚举数据
        Args:

        """

        super().__init__(*args, **kwargs)

    def __getattr__(self, attr):
        """
            获取属性的值，如果属性存在则返回，否则返回None,减少报错次数
        Args:
            attr: 要获取的属性
        Returns:
            返回属性值或者None
        """
        return self.get(attr)


class _CachedGManager(object):
    """
    缓存全局实例引用
    """

    _cache: WeakValueDictionary = weakref.WeakValueDictionary()

    def __new__(cls, *args, **kwargs):
        """

        Args:

        Returns:

        """
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __getattr__(self, attr):
        if attr in self._cache:
            return self._cache[attr]
        else:
            raise AttributeError("CachedGManager has no '{}'".format(attr))

    def __setattr__(self, attr, instance):
        self._cache[attr] = instance

    def clear(self, ):
        """
        清除所有缓存引用
        Args:

        Returns:

        """
        self._cache.clear()


g = _CachedGManager()


class Config(object):
    """
    config配置类

    用于类flask应用的配置
    Args:

    Returns:

    """

    DEBUG = False
    AELOG_CONSOLE = False
    ACCESS_LOG = False

    @classmethod
    def dict2attr(cls, dict_obj: Dict):
        """
        字典到属性的转换
        Args:
            dict_obj
        Returns:

        """
        for attr, user_config in dict_obj.items():
            user_config = UserConfig(user_config) if isinstance(user_config, MutableMapping) else user_config
            setattr(cls, attr.upper(), user_config)
        return cls
