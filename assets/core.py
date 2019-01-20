# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'

import json
from django.core.exceptions import ObjectDoesNotExist
from assets import models
from django.utils import timezone


class Asset(object):
    def __init__(self, request):
        self.request = request
        # mandatory_fields：必须的字段，有则合法，否则不合法
        self.mandatory_fields = ['sn', 'asset_id', 'asset_type']  # must contains 'sn' , 'asset_id' and 'asset_type'
        self.field_sets = {
            'asset': ['manufactory'],
            'server': ['model', 'cpu_count', 'cpu_core_count', 'cpu_model', 'raid_type', 'os_type', 'os_distribution',
                       'os_release'],
            'networkdevice': []
        }
        self.response = {  # 响应存放到对应列表中
            'error': [],
            'info': [],
            'warning': []
        }

    def response_msg(self, msg_type, key, msg):
        """
        响应数据
        :param msg_type: 消息类型
        :param key: key
        :param msg: 消息
        :return:
        """
        if msg_type in self.response:
            self.response[msg_type].append({key: msg})
        else:
            raise ValueError

    def mandatory_check(self, data, only_check_sn=False):
        """
        强制检查客户端数据是否有必须的字段
        :param data:
        :param only_check_sn:
        :return:
        """
        for field in self.mandatory_fields:  # mandatory_fields:['sn', 'asset_id', 'asset_type']
            if field not in data:
                self.response_msg('error', 'MandatoryCheckFailed',
                                  "The field [%s] is mandatory and not provided in your reporting data" % field)
        else:
            if self.response['error']: return False
        try:
            if not only_check_sn:  # 当only_check_sn为False时条件成立
                # 用id和sn获取数据
                self.asset_obj = models.Asset.objects.get(id=int(data['asset_id']), sn=data['sn'])
            else:  # 当only_check_sn为True时条件成立
                # 用sn获取数据
                self.asset_obj = models.Asset.objects.get(sn=data['sn'])
            return True

        except ObjectDoesNotExist as e:
            self.response_msg('error', 'AssetDataInvalid',
                              "Cannot find asset object in DB by using asset id [%s] and SN [%s] " % (
                                  data['asset_id'], data['sn']))
            self.waiting_approval = True  # 设置这条资产为待批准
            return False

    def get_asset_id_by_sn(self):
        '''
        When the client first time reports it's data to Server,it doesn't know
        it's asset id yet,so it will come to the server asks for the asset it first,
        then report the data again
        '''
        data = self.request.POST.get("asset_data")  # 获取客户端数据
        response = {}
        if data:
            try:
                data = json.loads(data)
                if self.mandatory_check(data, only_check_sn=True):
                    # the asset is already exist in DB,just return it's asset id to client
                    response = {'asset_id': self.asset_obj.id}
                else:
                    if hasattr(self, 'waiting_approval'):
                        # 通过标识'waiting_approval'判断是一个新资产
                        response = {
                            'needs_aproval': "this is a new asset,needs IT admin's approval to create the new asset id."}
                        self.clean_data = data
                        self.save_new_asset_to_approval_zone()  # 保存到数据库中
                        print(response)
                    else:
                        response = self.response
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
                response = self.response

        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")
            response = self.response
        return response

    def save_new_asset_to_approval_zone(self):
        '''
        当发现一个新资产，将资产保存到待存区等待管理员批准
        '''
        asset_sn = self.clean_data.get('sn')
        # get_or_create方法：数据不存在就创建一条，如果存在就把数据取出来
        asset_already_in_approval_zone = models.NewAssetApprovalZone.objects.get_or_create(
            sn=asset_sn,
            data=json.dumps(self.clean_data),
            manufactory=self.clean_data.get('manufactory'),
            model=self.clean_data.get('model'),
            asset_type=self.clean_data.get('asset_type'),
            ram_size=self.clean_data.get('ram_size'),
            cpu_model=self.clean_data.get('cpu_model'),
            cpu_count=self.clean_data.get('cpu_count'),
            cpu_core_count=self.clean_data.get('cpu_core_count'),
            os_distribution=self.clean_data.get('os_distribution'),
            os_release=self.clean_data.get('os_release'),
            os_type=self.clean_data.get('os_type')
        )
        return True

    def data_is_valid(self):
        data = self.request.POST.get("asset_data")
        if data:
            try:
                data = json.loads(data)
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")

    def __is_new_asset(self):
        """判断是否是新资产"""
        # 在通过mandatory检查时，确定会有'asset_type'字段
        if not hasattr(self.asset_obj, self.clean_data['asset_type']):
            return True
        else:
            return False

    def data_inject(self):
        '''
        将数据保存到数据库中，
        save data into DB,the data_is_valid() must returns True before call this function
        '''
        # self.reformat_components('slot',self.clean_data.get('ram'))
        # self.reformat_components('name',self.clean_data.get('nic'))
        if self.__is_new_asset():  # 判断是否是新资产
            print('\033[32;1m---new asset,going to create----\033[0m')

            self.create_asset()  # 创建资产
        else:  # asset already already exist , just update it
            print('\033[33;1m---asset already exist ,going to update----\033[0m')

            self.update_asset()  # 更新资产

    def data_is_valid_without_id(self):
        '''
        当客户端汇报的数据中的没有资产id，先运行这个函数
        when there's no asset id in reporting data ,goes through this function fisrt
        '''
        # 在视图的new_assets_approval函数已添加数据:request.POST['asset_data'] = obj.data
        data = self.request.POST.get("asset_data")  # 拿到客户端数据
        if data:
            try:
                data = json.loads(data)  # 数据保存在数据库是Json格式
                # push asset id into reporting data before doing the mandatory check
                asset_obj = models.Asset.objects.get_or_create(sn=data.get('sn'), name=data.get('sn'))
                data['asset_id'] = asset_obj[0].id  # 将资产id放入客户端汇报的数据中
                self.mandatory_check(data)  # 检查客户端数据是否有必须的字段
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")

    def reformat_components(self, identify_field, data_set):
        '''This function is used as workround for some components's data structor is big dict ,yet
        the standard structor is list,e.g:
        standard: [{
            "slot": "1I:1:1",
            "capacity": 300,
            "sn": "",
            "model": "",
            "enclosure": "0",
            "iface_type": "SAS"
        },
        {
            "slot": "1I:1:2",
            "capacity": 300,
            "sn": "",
            "model": "",
            "enclosure": "0",
            "iface_type": "SAS"
        }]
        but for some components such as ram:
        {"PROC 2 DIMM 1": {
            "model": "<OUT OF SPEC>",
            "capacity": 0,
            "sn": "Not Specified",
            "manufactory": "UNKNOWN"
        },}

        it uses key as identified field, the key is actually equals slot field in db model field, this unstandard
        data source should be dprecated in the future, now I will just reformat it as workround
        '''
        for k, data in data_set.items():
            data[identify_field] = k

    def __verify_field(self, data_set, field_key, data_type, required=True):
        """
        验证数据类型
        self.__verify_field(self.clean_data, 'model', str)
        :param data_set: 最初是来自请求中的资产数据：self.request.POST.get("asset_data")
        :param field_key: 字段值
        :param data_type: 数据类型
        :param required: 必须值
        :return:
        """
        field_val = data_set.get(field_key)
        # if field_val:   # field_val=0时,这样会判断为空
        # 在python中 None,  False, 空字符串"", 0, 空列表[], 空字典{}, 空元组()都相当于False
        if field_val is not None:  # 判断是否有数据，这是最好的写法
            try:
                data_set[field_key] = data_type(field_val)  # 将数据值转为对应数据类型(比如：str)，赋给键field_key
            except ValueError as e:
                # 如果转换失败做如下报错
                self.response_msg(
                    'error', 'InvalidField',
                    "The field [%s]'s data type is invalid, the correct data type should be [%s] " % (
                        field_key, data_type)  # model , str
                )
        elif required == True:  # 没有数据，提示没有提供相应的字段
            self.response_msg(
                'error', 'LackOfField',
                "The field [%s] has no value provided in your reporting data [%s]" % (
                    field_key, data_set)
            )

    def create_asset(self):
        '''基于资产类型创建资产'''
        func = getattr(self, '_create_%s' % self.clean_data['asset_type'])  # _create_server方法
        create_obj = func()

    def update_asset(self):
        """更新资产"""
        func = getattr(self, '_update_%s' % self.clean_data['asset_type'])  # 比如：'_update_server'
        create_obj = func()

    def _update_server(self):
        nic = self.__update_asset_component(
            data_source=self.clean_data['nic'],  # 客户端数据
            fk='nic_set',  # 通过asset对象反查的表名
            # 需更新的字段（不是所有字段都要更新）
            update_fields=['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding'],
            identify_field='macaddress'  # mac地址
        )
        disk = self.__update_asset_component(
            data_source=self.clean_data['physical_disk_driver'],
            fk='disk_set',
            update_fields=['slot', 'sn', 'model', 'manufactory', 'capacity', 'iface_type'],
            identify_field='slot'
        )
        ram = self.__update_asset_component(
            data_source=self.clean_data['ram'],
            fk='ram_set',
            update_fields=['slot', 'sn', 'model', 'capacity'],
            identify_field='slot'
        )
        cpu = self.__update_cpu_component()
        manufactory = self.__update_manufactory_component()
        server = self.__update_server_component()

    def _create_server(self):
        """创建服务器"""
        self.__create_server_info()  # 创建server信息
        self.__create_or_update_manufactory()  # 创建或更新生产厂商

        self.__create_cpu_component()
        self.__create_disk_component()
        self.__create_nic_component()  # 网卡
        self.__create_ram_component()  # 内存
        # 提示资产创建信息
        log_msg = "Asset [<a href='/admin/assets/asset/%s/' target='_blank'>%s</a>] has been created!" % (
            self.asset_obj.id, self.asset_obj)
        self.response_msg('info', 'NewAssetOnline', log_msg)  # 添加了一个'NewAssetOnline'信息提示是新资产上线

    def __create_server_info(self, ignore_errs=False):
        """
        创建server信息
        :param ignore_errs: 默认不忽略错误
        :return:
        """
        try:
            # 做验证确保clean_data里有model字段，且model是一个字符串
            self.__verify_field(self.clean_data, 'model', str)

            if not len(self.response['error']) or ignore_errs == True:  # 如果没有错误信息或忽略错误
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'raid_type': self.clean_data.get('raid_type'),
                    'model': self.clean_data.get('model'),
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }

                obj = models.Server(**data_set)
                # 将model字段从资产表移到server表中
                # obj.asset.model = self.clean_data.get('model')
                obj.save()
                return obj
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [server] %s' % str(e))

    def __create_or_update_manufactory(self, ignore_errs=False):
        """创建或更新生产商"""
        try:
            self.__verify_field(self.clean_data, 'manufactory', str)
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs == True:  # no processing when there's no error happend
                obj_exist = models.Manufactory.objects.filter(manufactory=manufactory)
                if obj_exist:
                    obj = obj_exist[0]
                else:  # create a new one
                    obj = models.Manufactory(manufactory=manufactory)
                    obj.save()
                self.asset_obj.manufactory = obj
                self.asset_obj.save()
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [manufactory] %s' % str(e))

    def __create_cpu_component(self, ignore_errs=False):
        """创建CPU组件"""
        try:
            # 验证字段
            self.__verify_field(self.clean_data, 'model', str)
            self.__verify_field(self.clean_data, 'cpu_count', int)
            self.__verify_field(self.clean_data, 'cpu_core_count', int)

            # 如果没有错误信息或忽略错误
            if not len(self.response['error']) or ignore_errs == True:  # no processing when there's no error happend
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'cpu_count': self.clean_data.get('cpu_count'),
                    'cpu_core_count': self.clean_data.get('cpu_core_count'),
                }

                obj = models.CPU(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [cpu] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                return obj
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [cpu] %s' % str(e))

    def __create_disk_component(self):
        """创建硬盘组件"""
        disk_info = self.clean_data.get('physical_disk_driver')
        if disk_info:
            for disk_item in disk_info:
                try:
                    self.__verify_field(disk_item, 'slot', str)
                    self.__verify_field(disk_item, 'capacity', float)
                    self.__verify_field(disk_item, 'iface_type', str)
                    self.__verify_field(disk_item, 'model', str)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_id': self.asset_obj.id,  # 资产id
                            'sn': disk_item.get('sn'),  # sn号
                            'slot': disk_item.get('slot'),  # 插槽
                            'capacity': disk_item.get('capacity'),  # 容量
                            'model': disk_item.get('model'),  # 模型
                            'iface_type': disk_item.get('iface_type'),  # 接口类型
                            'manufactory': disk_item.get('manufactory'),  # 生产商
                        }

                        obj = models.Disk(**data_set)
                        obj.save()

                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [disk] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'Disk info is not provied in your reporting data')

    def __create_nic_component(self):
        """创建网卡组件"""
        nic_info = self.clean_data.get('nic')
        if nic_info:
            for nic_item in nic_info:
                try:
                    self.__verify_field(nic_item, 'macaddress', str)  # 验证mac地址必须存在
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'name': nic_item.get('name'),
                            'sn': nic_item.get('sn'),
                            'macaddress': nic_item.get('macaddress'),
                            'ipaddress': nic_item.get('ipaddress'),
                            'bonding': nic_item.get('bonding'),  # 是否绑定（客户端检测）
                            'model': nic_item.get('model'),
                            'netmask': nic_item.get('netmask'),
                        }

                        obj = models.NIC(**data_set)
                        obj.save()

                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [nic] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'NIC info is not provied in your reporting data')

    def __create_ram_component(self):
        """创建内存组件"""
        ram_info = self.clean_data.get('ram')
        if ram_info:
            for ram_item in ram_info:
                try:
                    self.__verify_field(ram_item, 'capacity', int)  # 校对capacity字段，且值必须是int
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'slot': ram_item.get("slot"),
                            'sn': ram_item.get('sn'),
                            'capacity': ram_item.get('capacity'),
                            'model': ram_item.get('model'),
                        }

                        obj = models.RAM(**data_set)
                        obj.save()

                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [ram] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'RAM info is not provied in your reporting data')

    def __update_server_component(self):
        update_fields = ['model', 'raid_type', 'os_type', 'os_distribution', 'os_release']
        if hasattr(self.asset_obj, 'server'):
            self.__compare_component(
                model_obj=self.asset_obj.server,
                fields_from_db=update_fields,
                data_source=self.clean_data
            )
        else:
            self.__create_server_info(ignore_errs=True)

    def __update_manufactory_component(self):
        self.__create_or_update_manufactory(ignore_errs=True)

    def __update_cpu_component(self):
        update_fields = ['cpu_model', 'cpu_count', 'cpu_core_count']
        if hasattr(self.asset_obj, 'cpu'):
            self.__compare_component(
                model_obj=self.asset_obj.cpu,
                fields_from_db=update_fields,
                data_source=self.clean_data
            )
        else:
            self.__create_cpu_component(ignore_errs=True)

    def __update_asset_component(self, data_source, fk, update_fields, identify_field=None):
        '''
        更新资产组件
        :param data_source: 组件汇报数据的数据源
        :param fk: 使用什么关键字去找到主资产对象和每个资产组件的连接
        :param update_fields: 数据库中什么字段要对比和更新
        :param identify_field: 使用字段去认证资产组件，set是None意味着只有使用资产id去认证
        :return:
        '''
        print(data_source, update_fields, identify_field)
        try:
            component_obj = getattr(self.asset_obj, fk)
            if hasattr(component_obj, 'select_related'):  # this component is reverse m2m relation with Asset model
                objects_from_db = component_obj.select_related()  # 把数据从数据库取出来
                for obj in objects_from_db:
                    key_field_data = getattr(obj, identify_field)  # 通过反射拿到mac地址
                    # use this key_field_data to find the relative data source from reporting data
                    if type(data_source) is list:  # 如果数据源是一个列表
                        for source_data_item in data_source:  # 到客户端的数据源里去找到跟服务器数据库中key_field_data对应的条目
                            key_field_data_from_source_data = source_data_item.get(identify_field)
                            if key_field_data_from_source_data:  # 匹配上了对应的网卡
                                if key_field_data == key_field_data_from_source_data:
                                    self.__compare_component(
                                        model_obj=obj,
                                        fields_from_db=update_fields,
                                        data_source=source_data_item
                                    )
                                    break  # 已经根据identify_field找到客户端中对应的数据条目，且对比完了，后面的loop没必要继续了
                            else:  # key field data from source data cannot be none
                                self.response_msg('warning', 'AssetUpdateWarning',
                                                  "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                                      fk, identify_field))

                        else:  # 无法找到比对，资产组件应该是坏了或被手工改动
                            print('\033[33;1mError:cannot find any matches in source data by using key field val [%s],'
                                  'component data is missing in reporting data!\033[0m' % (key_field_data))
                            self.response_msg(
                                "error", "AssetUpdateWarning",
                                "Cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!" % (
                                    key_field_data)
                            )
                    elif type(data_source) is dict:  # deprecated
                        for key, source_data_item in data_source.items():
                            key_field_data_from_source_data = source_data_item.get(identify_field)
                            if key_field_data_from_source_data:
                                if key_field_data == key_field_data_from_source_data:  # find the matched source data for this component,then should compare each field in this component to see if there's any changes since last update
                                    self.__compare_component(
                                        model_obj=obj,
                                        fields_from_db=update_fields,
                                        data_source=source_data_item
                                    )
                                    break  # must break ast last ,then if the loop is finished , logic will goes for ..else part,then you will know that no source data is matched for by using this key_field_data, that means , this item is lacked from source data, it makes sense when the hardware info got changed. e.g: one of the RAM is broken, sb takes it away,then this data will not be reported in reporting data
                            else:  # key field data from source data cannot be none
                                self.response_msg('warning', 'AssetUpdateWarning',
                                                  "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                                      fk, identify_field))

                        else:  # couldn't find any matches, the asset component must be broken or changed manually
                            print(
                                '\033[33;1mWarning:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!\033[0m' % (
                                    key_field_data))
                    else:
                        print('\033[31;1mMust be sth wrong,logic should goes to here at all.\033[0m')
                # compare all the components from DB with the data source from reporting data
                self.__filter_add_or_deleted_components(  # 把服务器端、客户端获取的数据作对比
                    model_obj_name=component_obj.model._meta.object_name,  # 拿到表名，比如：'NIC'
                    data_from_db=objects_from_db,  # 从数据库获取的数据
                    data_source=data_source,  # 客户端的数据
                    identify_field=identify_field  # 唯一值
                )

            else:  # this component is reverse fk relation with Asset model
                pass
        except ValueError as e:
            print('\033[41;1m%s\033[0m' % str(e))

    def __filter_add_or_deleted_components(self, model_obj_name, data_from_db, data_source, identify_field):
        """
        对比过滤出要添加或删除的组件
        This function is filter out all component data in db but missing in reporting data, and all the data in reporting data but not in DB
        :param model_obj_name: 获取的表名
        :param data_from_db: 数据库获取的数据
        :param data_source: 客户端数据（字典）
        :param identify_field: 认证字段（唯一值）
        :return:
        """
        print(data_from_db, data_source, identify_field)
        # 创建一个列表保存所有客户端数据认证关键字
        data_source_key_list = []  # save all the identified keys from client data,e.g: [macaddress1,macaddress2]

        if type(data_source) is list:  # 判断是否是一个列表
            for data in data_source:  # 循环字典
                data_source_key_list.append(data.get(identify_field))
        elif type(data_source) is dict:  # 不太可能是字典（客户端发送的数据应该统一）
            for key, data in data_source.items():
                if data.get(identify_field):
                    data_source_key_list.append(data.get(identify_field))
                else:  # workround for some component uses key as identified field e.g: ram
                    data_source_key_list.append(key)
        print('-->identify field [%s] from db  :', data_source_key_list)
        print('-->identify[%s] from data source:', [getattr(obj, identify_field) for obj in data_from_db])

        data_source_key_list = set(data_source_key_list)
        # 列表生成式：循环数据库的数据，把每个对象通过反射形式获取唯一值identify_field，再set()设置值
        data_identify_val_from_db = set([getattr(obj, identify_field) for obj in data_from_db])

        # 只在db存在的数据：求差集，得到数据库存在客户端没有的数据
        data_only_in_db = data_identify_val_from_db - data_source_key_list  # delete all this from db
        # 只在客户端数据保存的数据：求差集，得到客户端存在而数据库没有的数据
        data_only_in_data_source = data_source_key_list - data_identify_val_from_db  # add into db

        print('\033[31;1mdata_only_in_db:\033[0m', data_only_in_db)
        print('\033[31;1mdata_only_in_data source:\033[0m', data_only_in_data_source)
        # 删除差集
        self.__delete_components(
            all_components=data_from_db,  # 数据库的数据
            delete_list=data_only_in_db,  # 要删除的唯一值列表
            identify_field=identify_field  # 去数据库查找的字段，eg.mac地址
        )
        # 添加差集
        if data_only_in_data_source:  # 如果客户端有多的差集
            self.__add_components(
                model_obj_name=model_obj_name,
                all_components=data_source,
                add_list=data_only_in_data_source,
                identify_field=identify_field
            )

    def __add_components(self, model_obj_name, all_components, add_list, identify_field):
        """
        添加组件
        :param model_obj_name: 模型对象名
        :param all_components: 客户端的源数据
        :param add_list: 要添加的唯一值列表
        :param identify_field: 去数据库查找的字段，eg.mac地址
        :return:
        """
        model_class = getattr(models, model_obj_name)  # 对应的类对象？
        will_be_creating_list = []
        print('--add component list:', add_list)
        if type(all_components) is list:
            for data in all_components:  # 循环所有组件
                if data[identify_field] in add_list:
                    # print data
                    will_be_creating_list.append(data)  # 添加到列表中
        elif type(all_components) is dict:  # deprecated
            for k, data in all_components.items():
                # workround for some components uses key as identified field ,e.g ram
                if data.get(identify_field):
                    if data[identify_field] in add_list:
                        # print k,data
                        will_be_creating_list.append(data)
                else:  # if the identified field cannot be found from data set,then try to compare the dict key
                    if k in add_list:
                        data[
                            identify_field] = k  # add this key into dict , because this dict will be used to create new component item in DB
                        will_be_creating_list.append(data)

        # creating components  创建组件
        try:
            for component in will_be_creating_list:
                data_set = {}
                for field in model_class.auto_create_fields:  # models中部分类有auto_create_fields字段
                    data_set[field] = component.get(field)  # 将字段名和值加入字典
                data_set['asset_id'] = self.asset_obj.id  # 加入关联的资产到字典
                obj = model_class(**data_set)
                obj.save()
                # 日志输出
                print('\033[32;1mCreated component with data:\033[0m', data_set)
                log_msg = "Asset[%s] --> component[%s] has justed added a new item [%s]" % (
                    self.asset_obj, model_obj_name, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                log_handler(self.asset_obj, 'NewComponentAdded', self.request.user, log_msg, model_obj_name)

        except Exception as e:
            print("\033[31;1m %s \033[0m" % e)
            log_msg = "Asset[%s] --> component[%s] has error: %s" % (self.asset_obj, model_obj_name, str(e))
            self.response_msg('error', "AddingComponentException", log_msg)

    def __delete_components(self, all_components, delete_list, identify_field):
        '''
        删除组件，从数据库all_components中删除所有delete_list中的对象
        All the objects in delete list will be deleted from DB
        :param all_components: 数据库的数据
        :param delete_list: 要删除的唯一值列表
        :param identify_field: 去数据库查找的字段
        :return:
        '''
        deleting_obj_list = []
        print('--deleting components', delete_list, identify_field)
        for obj in all_components:  # [nic1_obj, nic2_obj,...]
            val = getattr(obj, identify_field)  # 在对象中根据identify_field取出值
            if val in delete_list:  # 如果值在差集中
                deleting_obj_list.append(obj)  # 添加obj到待删除列表中

        for i in deleting_obj_list:  # 循环要删除的列表，执行删除操作
            log_msg = "Asset[%s] --> component[%s] --> is lacking from reporting source data, assume it has been removed or replaced,will also delete it from DB" % (
                self.asset_obj, i)  # 日志信息，xx数据不在汇报数据中，假设已被删除或替换，将其从数据库中删除
            self.response_msg('info', 'HardwareChanges', log_msg)
            log_handler(self.asset_obj, 'HardwareChanges', self.request.user, log_msg, i)  # 记录日志
            i.delete()  # 从数据库中删除

    def __compare_component(self, model_obj, fields_from_db, data_source):
        """
        组件对比
        :param model_obj:
        :param fields_from_db: update_fields
        :param data_source: source_data_item
        :return:
        """
        print('---going to compare:[%s]' % model_obj, fields_from_db)
        print('---source data:', data_source)
        for field in fields_from_db:
            val_from_db = getattr(model_obj, field)
            val_from_data_source = data_source.get(field)
            if val_from_data_source:  # 如果客户端数据源有这个数据
                # if type(val_from_db) is unicode:val_from_data_source = unicode(val_from_data_source)#no unicode in py3
                # if type(val_from_db) in (int,long):val_from_data_source = int(val_from_data_source) #no long in py3
                if type(val_from_db) in (int,):  # 如果数据库数据类型是int
                    val_from_data_source = int(val_from_data_source)  # 将客户端数据转换为int
                elif type(val_from_db) is float:
                    val_from_data_source = float(val_from_data_source)
                elif type(val_from_db) is str:
                    val_from_data_source = str(val_from_data_source).strip()
                if val_from_db == val_from_data_source:  # this field haven't changed since last update
                    pass
                    # print '\033[32;1m val_from_db[%s]  == val_from_data_source[%s]\033[0m' %(val_from_db,val_from_data_source)
                else:
                    print('\033[34;1m val_from_db[%s]  != val_from_data_source[%s]\033[0m' % (
                        val_from_db, val_from_data_source), type(val_from_db), type(val_from_data_source), field)
                    db_field = model_obj._meta.get_field(field)
                    db_field.save_form_data(model_obj, val_from_data_source)
                    model_obj.update_date = timezone.now()  # 时间更新
                    model_obj.save()
                    # 日志记录
                    log_msg = "Asset[%s] --> component[%s] --> field[%s] has changed from [%s] to [%s]" % (
                        self.asset_obj, model_obj, field, val_from_db, val_from_data_source)
                    self.response_msg('info', 'FieldChanged', log_msg)  # 返回给客户端（浏览器上显示）的消息
                    log_handler(self.asset_obj, 'FieldChanged', self.request.user, log_msg, model_obj)  # 真正记录的日志
            else:
                self.response_msg('warning', 'AssetUpdateWarning',
                                  "Asset component [%s]'s field [%s] is not provided in reporting data " % (
                                      model_obj, field))
        model_obj.save()


def log_handler(asset_obj, event_name, user, detail, component=None):
    '''
    记录日志方法
    (1,u'硬件变更'),
    (2,u'新增配件'),
    (3,u'设备下线'),
    (4,u'设备上线'),
    '''
    log_catelog = {
        1: ['FieldChanged', 'HardwareChanges'],
        2: ['NewComponentAdded'],
    }
    if not user.id:
        # user = models.UserProfile.objects.filter(is_admin=True).last()
        user = models.UserProfile.objects.filter(is_superuser=True).last()
    event_type = None
    for k, v in log_catelog.items():
        if event_name in v:
            event_type = k
            break
    log_obj = models.EventLog(  # 日志记录到EventLog表
        name=event_name,
        event_type=event_type,
        asset_id=asset_obj.id,
        component=component,
        detail=detail,
        user_id=user.id
    )
    log_obj.save()
