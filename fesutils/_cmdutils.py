#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/6 上午10:41
"""
import asyncio
import subprocess

from fesutils.err import CommandArgsError

__all__ = ("execute_shell", "async_execute_shell")


def execute_shell(name, cmd):
    """
    excute shell
    Args:
        name: 执行的命令名称
        cmd: 执行命令的实际内容
    Returns:

    """
    try:
        rs = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise CommandArgsError(f"{name} error, {str(e.output)}")
    else:
        return rs.decode(encoding="utf8")


async def async_execute_shell(cmd):
    """
    async excute shell
    Args:
        cmd: 要执行的命令字符串
    Returns:

    """
    process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    success_msg, error_msg = await process.stdout.read(), await process.stderr.read()
    returncode = await process.wait()
    if returncode == 0:
        return success_msg.decode()
    else:
        raise CommandArgsError(error_msg.decode())
