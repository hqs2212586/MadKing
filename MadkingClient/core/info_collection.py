# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'


from plugins import plugin_api
import json,platform,sys


class InfoCollection(object):
    """收集硬件信息"""
    def __init__(self):
        pass

    def get_platform(self):
        """获取平台"""
        os_platform = platform.system()  # 获取操作系统类型
        return os_platform

    def collect(self):
        os_platform = self.get_platform()   # 获取平台信息
        try:
            # 通过反射查看当前类下是否有相应的平台
            func = getattr(self, os_platform)   # Linux() 和 Windows()
            info_data = func()
            formatted_data = self.build_report_data(info_data)
            return formatted_data
        except AttributeError as e:
            sys.exit("Error:MadKing doens't support os [%s]! " % os_platform)

    def Linux(self):
        sys_info = plugin_api.LinuxSysInfo()

        return sys_info

    def Windows(self):
        sys_info = plugin_api.WindowsSysInfo()   # windows收集的数据
        # print(sys_info)
        # f = file('data_tmp.txt','wb')
        # f.write(json.dumps(sys_info))
        # f.close()
        return sys_info

    def build_report_data(self,data):

        #add token info in here before send

        return data