#!/usr/bin/env python
# -*-coding:utf-8-*-
# @Time : 2020/1/7
# @Author : Allen Woo
from flask_script import Manager
from apps.app import celery, app
from apps.init_core_module import init_core_module

"""
celery worker main
Don't del 'celery' obj
"""

init_core_module(
    app=app
)
manager = Manager(app)

