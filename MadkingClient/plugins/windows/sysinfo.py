# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'


import platform
import win32com
import wmi
import os


class Win32Info(object):
    def __init__(self):
        self.wmi_obj = wmi.WMI()
        self.wmi_server_obj = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        self.wmi_server_connector = self.wmi_server_obj.ConnectServer(".", "root\cimv2")

    def get_cpu_info(self):
        """获取cpu信息"""
        data = {}
        cpu_lists = self.wmi_obj.Win32_Processor()  # 列表对象
        cpu_core_count = 0

        for cpu in cpu_lists:
            cpu_core_count += cpu.NumberOfCores   # cpu核数
            cpu_model = cpu.Name   # cpu名称

        data["cpu_count"] = len(cpu_lists)   # cpu个数
        data["cpu_model"] = cpu_model
        data["cpu_core_count"] = cpu_core_count   # cpu核数
        return data

    def get_ram_info(self):
        data = []
        ram_collections = self.wmi_server_connector.ExecQuery("Select * from Win32_PhysicalMemory")
        for item in ram_collections:
            item_data = {}
            # print(item)
            mb = int(1024 * 1024)
            ram_size = int(item.Capacity) / mb
            item_data = {
                "slot": item.DeviceLocator.strip(),  # 插槽
                "capacity": ram_size,    # 容量
                "model": item.Caption,   # 型号
                "manufactory": item.Manufacturer,   # 厂商
                "sn": item.SerialNumber    # sn号
            }
            data.append(item_data)
        # for i in data:
        #     print(i)
        return {"ram": data}

    def get_server_info(self):
        computer_info = self.wmi_obj.Win32_ComputerSystem()[0]
        system_info = self.wmi_obj.Win32_OperationSystem()[0]
        data = {}
        data['manufactory'] = computer_info.Manufacturer
        data['model'] = computer_info.Model
        data['wake_up_type'] = computer_info.WakeUpType
        data['sn'] = system_info.SerialNumber
        # print(data)
        return data

    def get_disk_info(self):
        data = []
        for disk in self.wmi_obj.Win32_DiskDrive():
            # print(disk.Model,disk.Size,disk.DeviceID,disk.Name,disk.Index,disk.SerialNumber,disk.SystemName,disk.Description)
            item_data = {}
            iface_choices = ["SAS", "SCSI", "SATA", "SSD"]
            for iface in iface_choices:
                if iface in disk.Model:
                    item_data['iface_type'] = iface
                    break
            else:
                item_data['iface_type'] = 'unknown'
            item_data['slot'] = disk.Index
            item_data['sn'] = disk.SerialNumber
            item_data['mode'] = disk.Model
            item_data['manufactory'] = disk.Manufacturer
            item_data['capacity'] = int(disk.Size) / (1024*1024*1024)
            data.append(item_data)
        return {'physical_disk_driver': data}

    def get_nic_info(self):
        data = []
        for nic in self.wmi_obj.Win32_NetworkAdapterConfiguration():
            if nic.MACAddress is not None:
                item_data = {}
                item_data['macaddress'] = nic.MACAddress
                item_data['model'] = nic.Caption
                item_data['name'] = nic.Index
                if nic.IPAddress is not None:
                    item_data['ipaddress'] = nic.IPAddress[0]
                    item_data['netmask'] = nic.IPSubnet
                else:
                    item_data['ipaddress'] = ''
                    item_data['netmask'] = ''
                bonding = 0
                # print(nic.MACAddress, nic.IPAddress, nic.ServiceName, nic.Caption, nic.IPSubnet)
                # print(item_data)
                data.append(item_data)
        return {'nic': data}


def collect():
    data = {
        'os_type': platform.system(),
        'os_release': "%s %s %s " % (platform.release(), platform.architecture()[0], platform.version())
        'os_distribution': 'Microsoft',
        'asset_type': 'server'   # 资产类型写死
    }
    # data.update(cpuinfo())
    win32obj = Win32Info()
    # 更新字典data
    data.update(win32obj.get_cpu_info())
    data.update(win32obj.get_ram_info())
    data.update(win32obj).get_server_info()
    data.update(win32obj.get_disk_info())
    data.update(win32obj.get_nic_info())

    # for k, v in data.items():
    #     print(k, v)
    return data


if __name__ == "__main__":
    collect()




