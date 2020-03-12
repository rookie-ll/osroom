#!/usr/bin/env python3
# -*-coding:utf-8-*-
# @Time : 2017/11/1 ~ 2019/9/1
# @Author : Allen Woo
import os
import sys
from signal import signal, SIGCHLD, SIG_IGN
from pymongo.errors import OperationFailure
from apps.configs.config import CONFIG
from apps.configs.db_config import DB_CONFIG
from apps.core.db.config_mdb import DatabaseConfig
from apps.core.utils.sys_tool import update_pylib, add_user as add_user_process
from apps.sys_startup_info import start_info
from apps.startup_option import parameter_processing


start_info()
print("\033[1;36m [OSROOM] Staring...\033[0m")

# 参数处理
sys_argv = parameter_processing(sys_argv=sys.argv)
is_debug = sys_argv["is_debug"]
csrf_enabled = sys_argv["csrf_enabled"]
update_config = sys_argv["upd_conf"]
push_url = sys_argv["push_url"]
if "--dis-csrf" in sys.argv:
    sys.argv.remove("--dis-csrf")
if "-S" in sys.argv:
    sys.argv.remove("-S")
if "--upd-conf" in sys.argv:
    sys.argv.remove("--up-sys-conf")
if "--push-url" in sys.argv:
    sys.argv.remove("--push-url")

# 网站还未启动的时候, 临时连接数据库, 更新collections & 更新系统配置
from apps.core.utils.update_sys_data import update_mdb_collections, init_datas, compatible_processing, \
    update_mdbcolls_json_file
from apps.core.db.mongodb import MyMongo
database = DatabaseConfig()
mdbs = {}
for k, mdb_acc in DB_CONFIG["mongodb"].items():
    mdbs[k] = MyMongo()

"""
# 初始化mdbs给以下程序在网站启动前使用
# 初始化2次，因为第一次初始化是为了更新mdb的collections, 更新后，可能存在新的collections
"""
db_init = 2
while db_init:
    try:
        for name, mdb in mdbs.items():
            if db_init == 1:
                mdb.close()
            if name not in ["sys", "user", "web"]:
                msg = "[Error]: 由v1.x.x更新到v2.x.x需要请更新你的数据库配置文件apps/configs/db_config.py." \
                      "请参考同目录下的db_config_sample.py"
                print('\033[31m{}\033[0m'.format(msg))
                sys.exit()

            mdb.init_app(
                config_prefix=name.upper(),
                db_config=database.__dict__["{}_URI".format(name.upper())]
            )

    except OperationFailure as e:

        msg = "\n[Mongodb] *{}\nMongodb validation failure, the user name, " \
              "password mistake or database configuration errors.\n" \
              "Tip: to open database authentication configuration".format(e)
        print('\033[31m{}\033[0m'.format(msg))

        sys.exit(-1)
    if db_init == 2 and update_config:
        print(" * Check or update the database collection")
        update_mdb_collections(mdbs=mdbs)
    db_init -= 1

if update_config:
    # 2. 更新配置文件
    from apps.core.flask.update_config_file import update_config_file
    print(" * Update and sync config.py")
    r = update_config_file(mdbs=mdbs)
    if not r:
        print("[Error] Update profile error, check log sys_start.log")
        sys.exit(-1)
else:
    msgs = """
 * The following services need to be run in a non-debug state.
  Including the following services:
  - Automatic update of Mongodb collections.
  - Automatic update of website routing rights control.
  - Automatically update and merge system configuration.

  If you must use the --debug parameter, you can specify some parameters to run the services listed above.
  --up-conf: Automatically update and merge system configuration
                 and automatic update of Mongodb collections
  --push_url: Automatic update of website routing rights control.
  For a specific explanation, please see the osroom documentation.
      """
    print('\033[33m{}\033[0m'.format(msgs))

del CONFIG["py_venv"]

# 调用兼容程序step 1
compatible_processing(mdbs=mdbs, stage=1)

# 调用初始化数据
init_datas(mdbs=mdbs)

for mdb in mdbs.values():
    mdb.close()

# 启动网站
from flask_script import Manager
from apps.app import app
from apps.core.flask.module_import import module_import
from apps.init_core_module import init_core_module
from apps.configs.sys_config import MODULES, LOG_PATH

init_core_module(
    app,
    csrf_enabled=csrf_enabled,
    update_config=update_config,
    push_url=push_url
)
module_import(MODULES)
compatible_processing(mdbs=mdbs, stage=2)
manager = Manager(app)
if is_debug:
    print(" * Signal:(SIGCHLD, SIG_IGN).Prevent child processes from becoming [Defunct processes]."
          "(Do not need to comment out)")
    signal(SIGCHLD, SIG_IGN)


@manager.command
def add_user():
    update_mdb_collections(mdbs=mdbs)
    init_datas(mdbs=mdbs)
    add_user_process(mdbs=mdbs)


@manager.command
def dbcoll_to_file():
    """
    更新mdb collections到json文件中
    :return:
    """
    update_mdbcolls_json_file(mdbs=mdbs)


if __name__ == '__main__':
    """
    使用Flask 自带 server启动网站
    """
    print(" * Use the Web service that comes with Flask")
    if "--debug" not in sys.argv and "-D" not in sys.argv:
        # 更新python第三方类库
        print(" * Check or update Python third-party libraries")
        update_pylib()
    else:
        print(" * Using --debug, the system will not check Python dependencies")

        # Debug模式异步模块启动
        print(" * Celery worker...")
        try:
            shcmd = """ps -ef | grep celery_worker.celery | awk '{print $2}' | xargs kill -9"""
            r = os.system(shcmd)
        except Exception as e:
            print(e)
        shcmd = "celery -A celery_worker.celery beat -l info --loglevel=debug --logfile={logfile} >{logfile} 2>&1 &".format(
            logfile="{}/celery.log".format(LOG_PATH)
        )
        os.system(shcmd)
        shcmd = "celery worker -A celery_worker.celery --loglevel=debug --logfile={logfile} >{logfile} 2>&1 &".format(
            logfile="{}/celery.log".format(LOG_PATH)
        )
        os.system(shcmd)

    manager.run()
