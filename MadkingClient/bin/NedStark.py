# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'

import os, sys
import platform   # 该模块用于访问平台相关属性


# platform.system()返回系统/操作系统名称
if platform.system() == "Windows":
    BASE_DIR = '\\'.join(os.path.abspath(os.path.dirname(__file__)).split('\\')[:-1])
    print(BASE_DIR)
else:
    BASE_DIR = '/'.join(os.path.abspath(os.path.dirname(__file__)).split('/')[:-1])

sys.path.append(BASE_DIR)


from core import HouseStark


if __name__ == '__main__':
    # sys.argv：命令行参数List,第一个元素是程序本身路径
    HouseStark.ArgvHandler(sys.argv)   # 传递sys.argv参数给ArgvHandler类
