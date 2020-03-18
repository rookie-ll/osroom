#!/usr/bin/env python
# -*-coding:utf-8-*-
# @Time : 2020/03/18 22:11
# @Author : Allen Woo
import os

from apps.configs.sys_config import PROJECT_PATH, APPS_PATH

path = "{}/apps/admin_pages/pages/".format(PROJECT_PATH)
js_dir = "{}/apps/admin_pages/static/js/page_js".format(PROJECT_PATH)
for root, dirs, files in os.walk(path):

    for filename in files:
        if not filename.endswith(".html"):
            continue
        filepath = "{}/{}".format(root, filename)
        js_path = "{}.js".format(os.path.splitext(filepath)[0])
        js_path = "{}/{}".format(js_dir, js_path.split("pages/")[-1])
        print(filepath)
        print(js_path)
        html_lines = []
        wf = None
        with open(filepath) as rf:
            is_start = False
            is_end = False
            for line in rf.readlines():
                if line.strip() == "<script>":
                    is_start = True
                    is_end = False
                    temp_dir = os.path.split(js_path)[0]
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    wf = open(js_path, "w")
                    script_path ="""
<script src="%s?v={{g.site_global.site_config.STATIC_FILE_VERSION}}">
</script>"""%(js_path.replace(APPS_PATH, ""))
                    print(script_path)
                    html_lines.append(script_path)
                    continue
                elif line.strip() == "</script>" and is_start:
                    is_start = False
                    is_end = True
                    continue
                if is_start:
                    # print(line.strip())
                    wf.write(line)
                    continue
                html_lines.append(line)

        if wf:
            wf.close()
        with open(filepath, "w") as wff:
            wff.writelines(html_lines)
