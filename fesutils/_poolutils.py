#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-26 下午3:32
"""
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import aelog

__all__ = ("pool", "thread_pool", "pool_submit",)

# 执行任务的线程池
pool = thread_pool = ThreadPoolExecutor(multiprocessing.cpu_count() * 10 + multiprocessing.cpu_count())


def pool_submit(func: Callable, *args, task_name: str = "", **kwargs):
    """
    执行长时间任务的线程调度方法
    Args:
        func, *args, **kwargs
    Returns:

    """

    def callback_done(fn):
        """
        线程回调函数
        Args:

        Returns:

        """
        try:
            data = fn.result()
        except Exception as e:
            aelog.exception("error,{} return result: {}".format(task_name, e))
        else:
            aelog.info("{} return result: {}".format(task_name, data))

    future_result = thread_pool.submit(func, *args, **kwargs)
    future_result.add_done_callback(callback_done)
