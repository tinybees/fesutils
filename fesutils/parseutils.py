#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午6:51

文件解析工具类
"""

import sys

try:
    import yaml
except ImportError as e:
    raise ImportError(e)

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader  # type: ignore

__all__ = ("analysis_yaml",)


def analysis_yaml(full_conf_path: str):
    """
    解析yaml文件
    Args:
        full_conf_path: yaml配置文件路径
    Returns:

    """
    with open(full_conf_path, 'rt', encoding="utf8") as f:
        try:
            conf = yaml.load(f, Loader=Loader)
        except yaml.YAMLError as e:
            print("Yaml配置文件出错, {}".format(e))
            sys.exit()
    return conf
