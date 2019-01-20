# -*- coding:utf-8 -*-

from django.db import models
# from django.contrib.auth.models import User
from assets.myauth import UserProfile

# Create your models here.

# class UserProfile(User):
#     """用户信息"""
#     name = models.CharField("姓名", max_length=32)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         super(User.Meta)
#         verbose_name = "用户"
#         verbose_name_plural = "用户"


class Asset(models.Model):
    """资产信息表"""
    asset_type_choices = (
        ('server', u'服务器'),
        ('networkdevice', u'网络设备'),
        ('storagedevice', u'存储设备'),
        ('securitydevice', u'安全设备'),
        ('securitydevice', u'机房设备'),
        # ('switch', u'交换机'),
        # ('router', u'路由器'),
        # ('firewall', u'防火墙'),
        # ('storage', u'存储设备'),
        # ('NLB', u'NetScaler'),
        # ('wireless', u'无限AP'),
        ('software', u'软件资产'),
        # ('others', u'其他类'),
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, default='server')
    name = models.CharField(max_length=64, unique=True)

    # sn\manufactory\management_ip都是公共信息
    sn = models.CharField(u'资产SN号', max_length=128, unique=True)  # sn号唯一
    manufactory = models.ForeignKey('Manufactory', verbose_name=u'制造商', null=True, blank=True, on_delete=models.CASCADE)
    management_ip = models.GenericIPAddressField(u'管理IP', blank=True, null=True)  # 管理IP（带外）
    # model = models.ForeignKey('ProductModel', verbose_name=u'型号')
    # model = models.CharField(u'型号',max_length=128,null=True, blank=True )

    # blank字段为True则该字段允许不填
    # null字段为True则django用NULL在数据库存储空值
    contract = models.ForeignKey('Contract', verbose_name=u'合同', null=True, blank=True, on_delete=models.CASCADE)  # 很多机器属于一个合同
    trade_date = models.DateField(u'购买时间', null=True, blank=True)
    expire_date = models.DateField(u'过保修期', null=True, blank=True)
    price = models.FloatField(u'价格', null=True, blank=True)  # 用于成本核算
    business_unit = models.ForeignKey('BusinessUnit', verbose_name=u'所属业务线', null=True, blank=True, on_delete=models.CASCADE)
    # tags：多对多
    tags = models.ManyToManyField('Tag', blank=True)
    idc = models.ForeignKey('IDC', verbose_name=u'IDC机房', null=True, blank=True, on_delete=models.CASCADE)
    admin = models.ForeignKey('UserProfile', verbose_name=u'资产管理员', null=True, blank=True, on_delete=models.CASCADE)

    status_choices = (
        (0, '在线'),
        (1, '已下线'),
        (2, '未知'),
        (3, '故障'),
        (4, '备用'),
    )
    status = models.SmallIntegerField(choices=status_choices, default=0)
    # status = models.ForeignKey('Status', verbose_name = u'设备状态',default=1)
    # Configuration = models.OneToOneField('Configuration',verbose_name='配置管理',blank=True,null=True)
    memo = models.TextField(u'备注', null=True, blank=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)   # auto_now_add 自动创建
    update_date = models.DateTimeField(blank=True, auto_now=True)    # auto_now 更新自动变化

    class Meta:
        verbose_name = '资产总表'   # 中文显示
        verbose_name_plural = "资产总表"

    def __str__(self):
        return '<id:%s name:%s>' % (self.id, self.name)


class Server(models.Model):
    """服务器信息"""
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE)
    sub_asset_type_choices = {
        (0, "PC服务器"),   # 0,1,2介绍空间
        (1, "刀片服务器"),
        (2, "小型机")
    }
    created_by_choices = {
        ('auto', 'Auto'),   # 自动添加，不允许修改
        ('manual', 'Manual')   # 手动添加，准确率低，运行修改
    }
    created_by = models.CharField(choices=created_by_choices, max_length=32,
                                  default='auto')   # auto: auto created,   manual:created manually
    hosted_on = models.ForeignKey('self', related_name='hosted_on_server', blank=True, null=True, on_delete=models.CASCADE)  # for virtual server

    model = models.CharField(verbose_name=u'型号', max_length=128, null=True, blank=True)
    # 若有多个CPU，型号应该都是一致的，故没做ForeignKey

    # nic = models.ManyToManyField('NIC', verbose_name='网卡列表')
    raid_type = models.CharField(u'raid类型', max_length=512, blank=True, null=True)
    # 硬盘需要去去关联server，因此不能是多对多的关系
    # physical_disk_driver = models.ManyToManyField('Disk', verbose_name=u'硬盘', blank=True, null=True)

    os_type = models.CharField(u'操作系统类型', max_length=64, blank=True, null=True)
    os_distribution = models.CharField(u'发型版本', max_length=64, blank=True, null=True)
    os_release = models.CharField(u'操作系统版本', max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = "服务器"
        # together = ["sn", "asset"]

    def __str__(self):
        return '%s sn:%s' % (self.asset.name, self.asset.sn)


class SecurityDevice(models.Model):
    """安全设备"""
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type_choices = (
        (0, '防火墙'),
        (1, '入侵检测设备'),
        (2, '互联网网关'),
        (3, '运维审计系统'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name="服务器类型", default=0)

    def __str__(self):
        return self.asset.id


class NetworkDevice(models.Model):
    """网络设备"""
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type_choices = (
        (0, '路由器'),
        (1, '交换机'),
        (2, '负载均衡'),
        (3, 'VPN设备')
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name="网络设备类型", default=0)

    vlan_ip = models.GenericIPAddressField(u'VlanIP', blank=True, null=True)
    intranet_ip = models.GenericIPAddressField(u'内网IP', blank=True, null=True)
    model = models.CharField(u'型号', max_length=128, null=True, blank=True)
    firmware = models.CharField('固件', max_length=64, blank=True, null=True)
    port_num = models.SmallIntegerField(u'端口个数', null=True, blank=True)
    device_detail = models.TextField(u'设置详细配置', null=True, blank=True)

    class Meta:
        verbose_name = '网络设备'
        verbose_name_plural = '网络设备'


class Software(models.Model):
    """只存储公司购买的软件"""
    os_types_choice = (
        (0, 'OS'),
        (1, '办公\开发软件'),
        (2, '业务软件'),
    )
    license_num = models.IntegerField(verbose_name="授权数")   # 授权个数
    # os_distribution_choices = (('windows','Windows'),
    #                            ('centos','CentOS'),
    #                            ('ubuntu', 'Ubuntu'))
    # type = models.CharField(u'系统类型', choices=os_types_choice, max_length=64,help_text=u'eg. GNU/Linux',default=1)
    # distribution = models.CharField(u'发型版本', choices=os_distribution_choices,max_length=32,default='windows')
    version = models.CharField(u'软件/系统版本', max_length=64, help_text=u'eg. CentOS release 6.5 (Final)', unique=True)

    # language_choices = (('cn',u'中文'),
    #                     ('en',u'英文'))
    # language = models.CharField(u'系统语言',choices = language_choices, default='cn',max_length=32)
    # #version = models.CharField(u'版本号', max_length=64,help_text=u'2.6.32-431.3.1.el6.x86_64' )


class Disk(models.Model):
    """存储硬盘信息"""
    # ForeignKey.on_delete：当一个model对象的ForeignKey关联的对象被删除时，默认情况下此对象也会一起被级联删除的。
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)  # 统一从asset调用
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    slot = models.CharField(u'插槽位', max_length=64)
    manufactory = models.CharField(u'制造商', max_length=64, blank=True, null=True)  # 制造商信息直接存在型号中
    model = models.CharField(u'磁盘型号', max_length=128, blank=True, null=True)
    capacity = models.FloatField(u'磁盘容量GB')
    disk_iface_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD')
    )

    iface_type = models.CharField(u'接口类型', max_length=64, choices=disk_iface_choice, default='SAS')
    memo = models.TextField(u'备注', blank=True, null=True)
    # 硬盘创建时间  硬盘更新时间
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)
    # 自动创建的字段
    auto_create_fields = ['sn', 'slot', 'manufactory', 'model', 'capacity', 'iface_type']

    class Meta:
        # unique_together:联合唯一，相当于数据库的联合约束
        unique_together = ("asset", "slot")   # 资产和插槽位，两个字段不能同时重复
        verbose_name = "硬盘"
        verbose_name_plural = "硬盘"

    def __str__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id, self.slot, self.capacity)


class NIC(models.Model):
    """存储网卡信息"""
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)  # 存储各种资产的网卡，不区分服务器、PC等
    # server = models.ForeignKey('Server')
    name = models.CharField(u'网卡名', max_length=64, blank=True, null=True)
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    model = models.CharField(u'网卡型号', max_length=128, blank=True, null=True)
    macaddress = models.CharField(u'MAC', max_length=64, unique=True)  # mac地址

    # GenericIPAddressField：ip v4和ip v6地址表示，ipv6遵循RFC 4291section 2.2,
    ipaddress = models.GenericIPAddressField(u'IP', blank=True, null=True)
    netmask = models.CharField(max_length=64, blank=True, null=True)
    bonding = models.CharField(max_length=64, blank=True, null=True)  # 网卡绑定
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    auto_create_fields = ['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding']

    class Meta:
        verbose_name = u'网卡'
        verbose_name_plural = u'网卡'
        # unique_together = ('asset_id', 'slot')
        unique_together = ('asset', 'macaddress')

    def __str__(self):
        return '%s:%s' % (self.asset_id, self.macaddress)


class RAM(models.Model):
    """内存信息"""
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    model = models.CharField(u'内存型号', max_length=128)
    slot = models.CharField(u'插槽', max_length=64)
    capacity = models.IntegerField(u'内存大小(MB)')
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)

    auto_create_fields = ['sn', 'slot', 'model', 'capacity']

    class Meta:
        verbose_name = "RAM"
        verbose_name_plural = "RAM"
        unique_together = ("asset", "slot")

    def __str__(self):
        return '%s:%s:%s' % (self.asset_id, self.slot, self.capacity)


class CPU(models.Model):
    """CPU信息"""
    # 一个机器的CPU型号必须完全一样
    asset = models.OneToOneField("Asset", on_delete=models.CASCADE)   # 一台机器对应一种CPU，不需要做多对多的对应
    cpu_model = models.CharField(u'CPU型号', max_length=128, blank=True)
    cpu_count = models.SmallIntegerField(u'物理CPU个数')
    cpu_core_count = models.SmallIntegerField(u'cpu核数')
    memo = models.TextField(u'备注', null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        # CPU与机器已经是一对一了，因此这里不需要联合唯一了
        verbose_name = "CPU部件"
        verbose_name_plural = "CPU部件"

    def __str__(self):
        return self.cpu_model


class RaidAdaptor(models.Model):
    """raid卡信息"""
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)    # 关联资产,多个raid卡对应一个机器
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    slot = models.CharField(u'插口', max_length=64)
    model = models.CharField(u'型号', max_length=64, blank=True, null=True)
    memo = models.TextField(u'备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("asset", "slot")   # 联合唯一：资产设备和插槽

    def __str__(self):
        return self.name

class Manufactory(models.Model):
    """厂商"""
    manufactory = models.CharField(u'厂商名称', max_length=64, unique=True)
    support_num = models.CharField(u'支持电话', max_length=30, blank=True)
    memo = models.CharField(u'备注', max_length=128, blank=True)

    class Meta:
        verbose_name = "厂商"
        verbose_name_plural = "厂商"

    def __str__(self):
        return self.manufactory


class BusinessUnit(models.Model):
    """业务线"""
    parent_unit = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Contract(models.Model):
    """合同信息"""
    sn = models.CharField(u'合同号', max_length=128, unique=True)
    name = models.CharField(u'合同名称', max_length=64)
    memo = models.TextField(u'备注', blank=True, null=True)
    price = models.IntegerField(u'合同金额')
    detail = models.TextField(u'合同详细', blank=True, null=True)
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    license_num = models.IntegerField(u'license数量', blank=True)
    create_date = models.DateField(auto_now_add=True)
    update_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "合同"
        verbose_name_plural = "合同"

    def __str__(self):
        return self.name


class IDC(models.Model):
    """IDC机房信息"""
    name = models.CharField(u'机房名称', max_length=64, unique=True)
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = '机房'
        verbose_name_plural = '机房'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """资产标签信息"""
    name = models.CharField('Tag name', max_length=32, unique=True)
    creator = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    create_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventLog(models.Model):
    """事件日志信息"""
    name = models.CharField(u'事件名称', max_length=100)
    event_type_choices = (
        (1, u'硬件变更'),
        (2, u'新增配件'),
        (3, u'设备下线'),
        (4, u'设备上线'),
        (5, u'定期维护'),
        (6, u'业务上线\更新\变更'),
        (7, u'其它')
    )
    event_type = models.SmallIntegerField(u'事件类型', choices=event_type_choices)
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    component = models.CharField('事件子项', max_length=255, blank=True, null=True)
    detail = models.TextField(u'事件详情')
    date = models.DateTimeField(u'事件时间', auto_now_add=True)
    user = models.ForeignKey('UserProfile', verbose_name=u'事件源', on_delete=models.CASCADE)
    memo = models.TextField(u'备注', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "事件记录"
        verbose_name_plural = "事件记录"

    def colored_event_type(self):
        if self.event_type == 1:
            cell_html = '<span style="background: orange;">%s</span>'
        elif self.event_type == 2:
            cell_html = '<span style="background: yellowgreen;">%s</span>'
        else:
            cell_html = '<span>%s</span>'
        return cell_html % self.get_event_type_display()

    colored_event_type.allow_tags = True
    colored_event_type.short_description = u'事件类型'


class NewAssetApprovalZone(models.Model):
    """新资产待审批区：客户端的数据会暂时保存在这个临时表里"""
    sn = models.CharField(u'资产SN号', max_length=128, unique=True)
    asset_type_choices = (
        ('server', u'服务器'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('storage', u'防火墙'),
        ('NLB', u'存储设备'),
        ('wireless', u'NetScaler'),
        ('software', u'无线AP'),
        ('others', u'其他类')
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, blank=True)  # 资产类型
    manufactory = models.CharField(max_length=64, blank=True, null=True)  # 厂商
    model = models.CharField(max_length=128, blank=True, null=True)
    ram_size = models.IntegerField(blank=True, null=True)
    cpu_model = models.CharField(max_length=128, blank=True, null=True)
    cpu_count = models.IntegerField(blank=True, null=True)
    cpu_core_count = models.IntegerField(blank=True, null=True)
    os_distribution = models.CharField(max_length=64, blank=True, null=True)
    os_type = models.CharField(max_length=64, blank=True, null=True)
    os_release = models.CharField(max_length=64, blank=True, null=True)

    data = models.TextField(u'资产数据')    # 客户端收集的资产数据
    date = models.DateTimeField(u'汇报日期', auto_now_add=True)
    approved = models.BooleanField(u'已批准', default=False)   # 用户审批，默认是未批准
    approved_by = models.ForeignKey('UserProfile', verbose_name=u'批准人', blank=True, null=True, on_delete=models.CASCADE)
    approved_date = models.DateTimeField(u'批准日期', blank=True, null=True)

    def __str__(self):
        return self.sn

    class Meta:
        verbose_name = '新上线待批准资产'
        verbose_name_plural = '新上线待批准资产'

