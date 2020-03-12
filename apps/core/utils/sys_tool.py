#!/usr/bin/env python
# -*-coding:utf-8-*-
# @Time : 2017/11/1 ~ 2019/9/1
# @Author : Allen Woo
import json
import os
import re
import sys
import subprocess
from getpass import getpass
from copy import deepcopy
import requests
from apps.configs.sys_config import PROJECT_PATH, SUPER_PER


def copy_config_to_sample():
    """
    复制db_account.py到db_account_sample,　并把密码替换掉，以免暴露到网上
    """

    from apps.configs.db_config import DB_CONFIG

    # 复制db_config.py 到　db_config_sample.py
    local_config = deepcopy(DB_CONFIG)
    for k, v in local_config.items():
        if isinstance(v, dict):
            for k1, v1 in v.items():
                if k1 == "password":
                    v[k1] = "<Your password>"
                elif isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == "password":
                            v1[k2] = "<Your password>"

    # 复制配置文件为sample配置文件
    info = """# -*-coding:utf-8-*-\n__author__ = "Allen Woo"\n"""
    temp_conf = str(json.dumps(local_config, indent=4, ensure_ascii=False))
    wf = open("{}/apps/configs/db_config_sample.py".format(PROJECT_PATH), "wb")
    wf.write(bytes(info, "utf-8"))
    wf.write(bytes("DB_CONFIG = ", "utf-8"))
    wf.write(
        bytes(
            temp_conf.replace(
                "false",
                "False").replace(
                "true",
                "True").replace(
                    "null",
                    "None"),
            "utf-8"))
    wf.close()
    print("It has been updated db_config_sample.py")


def add_user(mdbs):
    """
    初始化root用户角色, 管理员, 管理员基本资料

    :return:
    """
    from werkzeug.security import generate_password_hash
    from apps.utils.validation.str_format import email_format_ver, password_format_ver
    from apps.modules.user.models.user import user_model
    from apps.modules.user.process.get_or_update_user import get_one_user_mfilter, update_one_user, insert_one_user

    print(' * [User] add')
    is_continue = False
    while True:
        username = input("Input username:")
        if re.search(r"[\.\*#\?]+", username):
            print(
                "[Warning]: The name format is not correct,You can't use '.','*','#','?'\n")
        else:
            break

    while not is_continue:
        email = input("Input email:")
        s, r = email_format_ver(email)
        if not s:
            print("[Warning]: {}".format(r))
        else:
            break

    while not is_continue:
        password = getpass("Input password(Password at least 8 characters):")
        s, r = password_format_ver(password)
        if not s:
            print("[Warning]: {}\n".format(r))
        else:
            break
    try:
        mdbs["user"].db.create_collection("role")
        print(' * Created role collection')
    except BaseException:
        pass
    try:
        mdbs["user"].db.create_collection("user")
        print(' * Created user collection')
    except BaseException:
        pass

    # 初始化角色
    root_per = SUPER_PER
    role_root = mdbs["user"].db.role.find_one({"permissions": root_per})
    if not role_root:
        print(" * Create root role...")
        r = mdbs["user"].db.role.insert_one({"name": "Root",
                                         "default": 0,
                                         "permissions": root_per,
                                         "instructions": 'Root'})

        if r.inserted_id:
            print("Create root user role successfully")
        else:
            print("[Error] Failed to create superuser role")
            sys.exit(-1)

        root_id = r.inserted_id
    else:
        root_id = role_root['_id']

    password_hash = generate_password_hash(password)
    user = get_one_user_mfilter(username=username, email=email, op="or")
    if user:
        update_one_user(user_id=str(user["_id"]),
                        updata={"$set": {"password": password_hash,
                                         "role_id": str(root_id)}})
        print(" * This user already exists, updated password.")
    else:
        print(' * Create root user...')
        user = user_model(
            username=username,
            email=email,
            password=password,
            custom_domain=-1,
            role_id=str(root_id),
            active=True)
        r = insert_one_user(updata=user)
        if r.inserted_id:
            print(" * Create a root user role successfully")
        else:
            print(" * [Error] Failed to create a root user role")
            sys.exit(-1)

    # To create the average user role
    average_user = mdbs["user"].db.role.find_one({"permissions": 1})
    if not average_user:
        print(" * Create the average user role...")
        r = mdbs["user"].db.role.insert_one({
            "name": "User",
            "default": 1,
            "permissions": 1,
            "instructions": 'The average user',
        })
        if r.inserted_id:
            print(" * Create a generic user role successfully")
        else:
            print(" * Failed to create a generic user role")

    role = mdbs["user"].db.role.find_one({"_id": root_id})
    hidden_password = "{}****{}".format(password[0:2], password[6:])
    print('The basic information is as follows')
    print('Username: {}\nEmail: {}\nUser role: {}\nPassword: {}'.format(
        username, email, role["name"], hidden_password))
    print('End')
    sys.exit()


def update_pylib(venv_path=True, latest=False):
    """
    更新python环境库
    :param input_venv_path:
    :return:
    """
    if venv_path == "default":
        input_str = input(
            "Already running this script in your project python virtual environment?(yes/no):\n"
        )
        if input_str.upper() == "YES":
            venv_path = None
        else:
            venv_path = input("Enter a virtual environment:\n")
    elif venv_path == "null":
        venv_path = None

    if venv_path:
        if os.path.exists("{}/bin/activate".format(venv_path)):
            venv = ". {}/bin/activate && ".format(venv_path)
        else:
            venv = ". {}/bin/activate && ".format(sys.prefix)
    else:
        venv = ""

    # 检查网络情况
    is_time_out = False
    try:
        requests.get("https://www.bing.com/", timeout=10)
    except Exception as e:
        is_time_out = True
        print(e)
    if not is_time_out:
        print(" * Update pip...")
        s, r = subprocess.getstatusoutput("{}pip3 install -U pip".format(venv))
        print("   {}".format(r))
    else:
        print(" ** Connection to external network timeout")
    s, r = subprocess.getstatusoutput("{}pip3 freeze".format(venv))
    venv_libs = r.split()
    with open("{}/requirements.txt".format(PROJECT_PATH)) as rf:
        # req_file_libs
        req_file_libs = rf.read().split()

    # 查找需要安装的包
    if latest:
        install_list = req_file_libs
    else:
        install_list = list(set(req_file_libs).difference(set(venv_libs)))

    for pylib in install_list[:]:
        if "==" not in pylib:
            install_list.remove(pylib)

    if install_list:
        msg = " * To install the following libs"
        print(msg)
        install_s = " ".join(install_list)
        print("   {}".format(install_s))
        if not venv_path:
            pass

    install_failed = []
    if not is_time_out:
        for sf in install_list:
            if latest:
                sf = sf.split("==")[0]
            shcmd = "{}pip3 install -U {}".format(venv, sf)
            print(shcmd)
            s, r = subprocess.getstatusoutput(shcmd)
            if s:
                install_failed.append(sf)

        for sf in install_failed:
            s, r = subprocess.getstatusoutput(
                "{}pip3 install -U {}".format(venv, sf))
            if not s:
                install_failed.remove(sf)

        if install_failed:
            msg = " * Installation failed library, please manually install"
            print(msg)
            print(install_failed)

    # 查找需要卸载的包
    s, r = subprocess.getstatusoutput("{}pip3 freeze".format(venv))
    venv_libs = r.split()
    uninstall_list = list(set(venv_libs).difference(set(req_file_libs)))
    for sf in uninstall_list[:]:
        if "==" not in sf:
            uninstall_list.remove(sf)

    if uninstall_list:
        msg = " * Now don't need python library:"
        print(msg)
        uninstall_s = " ".join(uninstall_list)
        print("   {}".format(uninstall_s))
        if not venv_path:
            pass


