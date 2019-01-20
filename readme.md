## 一、数据结构设计和生成

模型文件所在目录：MadKing/assets/models.py

执行数据迁移：
```bash
(python37) bash-3.2$ python manage.py makemigrations
(python37) bash-3.2$ python manage.py migrate
```

创建admin用户：
```bash
(python37) bash-3.2$ python manage.py createsuperuser
Username (leave blank to use 'hqs'): hqs
Email address: 
Password: 
Password (again): 
Error: Blank passwords aren't allowed.   # 密码不能为空
Password: 
Password (again): 
This password is too short. It must contain at least 8 characters.   # 密码过于简单可强制同意
This password is too common.
This password is entirely numeric.
Bypass password validation and create user anyway? [y/N]: y
Superuser created successfully.
```

## 二、CMDB客户端
http协议发送agent节点信息。
客户端代码存放地址：MadKing/MadkingClient

### 1、客户端子目录介绍
bin：入口程序
conf：配置
core：代码
logs：日志
plugins：插件
var：

### 2、python安装wmi模块
微软官网对WMI的介绍：
[WMI官网介绍](https://docs.microsoft.com/zh-cn/windows/desktop/WmiSdk/wmi-start-page)

WMI的全称是Windows Management Instrumentation，即Windows管理规范。
它是Windows操作系统上管理数据和操作的基础设施。我们可以使用WMI脚本或者应用自动化管理任务等。

WMI并不原生支持Python。不过没有关系，它支持VB，而Python中的两个第三方库wmi和win32com，均能以类似VB的用法来使用。

### 3、linux客户端收集数据并发送

```bash
[root@MiWiFi-R4C-srv bin]# python NedStark.py collect_data

[root@MiWiFi-R4C-srv bin]# python NedStark.py report_asset
token format:[hqs@qq.com
1546107460
hqs123]
token :[a0e96c23abae886cca8bec533a50f034]
Connecting [http://192.168.31.28:8000/asset/report/asset_with_no_asset_id/?user=hqs@qq.com&timestamp=1546107460&token=ae886cc], it may take a minute
[post]:[http://192.168.31.28:8000/asset/report/asset_with_no_asset_id/?user=hqs@qq.com&timestamp=1546107460&token=ae886cc] response:
{u'needs_aproval': u"this is a new asset,needs IT admin's approval to create the new asset id."}
```

## 三、服务端解析


### 2、API安全认证
