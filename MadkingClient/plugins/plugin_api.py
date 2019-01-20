# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'


from plugins.linux import sysinfo     # 引入linux下的sysinfo


def LinuxSysInfo():
    #print __file__
    return  sysinfo.collect()


def WindowsSysInfo():
    # 引入windows下的sysinfo
    from plugins.windows import sysinfo as win_sysinfo
    return win_sysinfo.collect()

