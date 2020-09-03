#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午6:43
"""
import atexit
import os
from typing import Callable

import aelog

try:
    import redis
    from redis.exceptions import RedisError
except ImportError as ex:
    raise ImportError(f"please pip install redis>=3.0.0 {ex}")

try:
    from flask import Flask
except ImportError as ex:
    raise ImportError(f"please pip install Flask {ex}")

from ._wraputils import ignore_error

__all__ = ("apscheduler_warkup_job", "apscheduler_start")


# noinspection PyProtectedMember
def apscheduler_warkup_job(scheduler):
    """
    唤醒job
    Args:

    Returns:

    """
    scheduler._scheduler.wakeup()


# noinspection PyProtectedMember
def apscheduler_start(app_: Flask, scheduler, is_warkup: bool = True, warkup_func: Callable = None,
                      warkup_seconds: int = 3600):
    """
    apscheduler的启动方法，利用redis解决多进程多实例的问题

    warkup_func可以包装apscheduler_warkup_job即可
    def warkup_func():
        apscheduler_warkup_job(scheduler)  # 这里的scheduler就是启动后的apscheduler全局实例
    Args:
        app_: app应用实例
        scheduler: apscheduler的调度实例
        is_warkup: 是否定期发现job，用于非运行scheduler进程添加的job
        warkup_func: 唤醒的job函数，可以包装apscheduler_warkup_job
        warkup_seconds: 定期唤醒的时间间隔
    Returns:

    """

    def remove_apscheduler():
        """
        移除redis中保存的标记
        Args:

        Returns:

        """
        rdb_ = None
        try:
            rdb_ = redis.StrictRedis(
                host=app_.config["ECLIENTS_REDIS_HOST"], port=app_.config["ECLIENTS_REDIS_PORT"],
                db=2, password=app_.config["ECLIENTS_REDIS_PASSWD"], decode_responses=True)
        except RedisError as err:
            aelog.exception(err)
        else:
            with ignore_error():
                rdb_.delete("apscheduler")
                aelog.info(f"当前进程{os.getpid()}清除redis[2]任务标记[apscheduler].")
        finally:
            if rdb_:
                rdb_.connection_pool.disconnect()

    try:
        from flask_apscheduler import APScheduler
        if not isinstance(scheduler, APScheduler):
            raise ValueError("scheduler类型错误")
    except ImportError as e:
        raise ImportError(f"please install flask_apscheduler {e}")

    rdb = None
    try:
        rdb = redis.StrictRedis(
            host=app_.config["ECLIENTS_REDIS_HOST"], port=app_.config["ECLIENTS_REDIS_PORT"],
            db=2, password=app_.config["ECLIENTS_REDIS_PASSWD"], decode_responses=True)
    except RedisError as e:
        aelog.exception(e)
    else:
        with rdb.lock("apscheduler_lock"):
            if rdb.get("apscheduler") is None:
                rdb.set("apscheduler", "apscheduler")
                scheduler.start()
                if is_warkup and callable(warkup_func):
                    scheduler.add_job("warkup", warkup_func, trigger="interval", seconds=warkup_seconds,
                                      replace_existing=True)
                    aelog.info(f"当前进程{os.getpid()}启动定时任务成功,设置redis[2]任务标记[apscheduler],"
                               f"任务函数为{warkup_func.__name__}.")
                atexit.register(remove_apscheduler)
            else:
                scheduler._scheduler.state = 2
                aelog.info(f"其他进程已经启动了定时任务,当前进程{os.getpid()}不再加载定时任务.")
    finally:
        if rdb:
            rdb.connection_pool.disconnect()
