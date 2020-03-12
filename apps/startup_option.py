#!/usr/bin/env python
# -*-coding:utf-8-*-
# @Time : 2020/03/12 19:37
# @Author : Allen Woo
import os

from apps.configs.sys_config import PROJECT_PATH


def parameter_processing(sys_argv):
    """
    额外的特殊参数处理
    :param sys_argv:
    :return:
    """
    result = {
        "is_debug": True,
        "csrf_enabled": True,
        "upd_conf": True,
        "push_url": True
    }
    # debug
    if "--debug" not in sys_argv and "-D" not in sys_argv:
        result["is_debug"] = False
    else:
        result["upd_conf"] = False
        result["push_url"] = False

    # other
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        sys_argv_str = " ".join(list(sys_argv))
        with open("{}/.temp_option".format(PROJECT_PATH), 'w') as wf:
            wf.write(sys_argv_str)
    else:
        with open("{}/.temp_option".format(PROJECT_PATH)) as rf:
            sys_argv = rf.read()
            sys_argv = sys_argv.split(" ")

    if "--dis-csrf" in sys_argv or "-S" in sys_argv:
        result["csrf_enabled"] = False
    if "--up-conf" in sys_argv:
        result["upd_conf"] = True
    if "--push-url" in sys_argv:
        result["push_url"] = True
    result["sys_argv"] = sys_argv
    return result

