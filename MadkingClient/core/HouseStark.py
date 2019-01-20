# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'

import urllib.request
import urllib.parse
import sys, os, json, datetime
from core import info_collection
from conf import settings
from core import api_token


class ArgvHandler(object):
    def __init__(self, argv_list):
        self.argvs = argv_list
        self.parse_argv()

    def parse_argv(self):
        if len(self.argvs) > 1:
            if hasattr(self, self.argvs[1]):
                func = getattr(self,self.argvs[1])
                func()
            else:
                # 如果输入的命令参数不正确，打印帮助信息
                self.help_msg()
        else:
            # 如果没有输入命令参数，打印帮助信息
            self.help_msg()

    def help_msg(self):
        msg = '''
        collect_data       收集资产数据
        run_forever
        get_asset_id       收集资产id
        report_asset       汇报资产数据到服务器 
        '''
        print(msg)

    def collect_data(self):
        """收集硬件信息"""
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        #print asset_data

    def run_forever(self):
        pass

    def __attach_token(self,url_str):
        '''generate md5 by token_id and username,and attach it on the url request'''
        user = settings.Params['auth']['user']
        token_id = settings.Params['auth']['token']

        md5_token,timestamp = api_token.get_token(user,token_id)
        url_arg_str = "user=%s&timestamp=%s&token=%s" %(user,timestamp,md5_token)
        if "?" in url_str:#already has arg
            new_url = url_str + "&" + url_arg_str
        else:
            new_url = url_str + "?" + url_arg_str
        return  new_url
        #print(url_arg_str)

    def __submit_data(self,action_type,data,method):
        """
        发送数据到服务器
        :param action_type:  url
        :param data: 具体要发送的数据
        :param method: get/post
        :return:
        """
        if action_type in settings.Params['urls']:   # 比对资产表接口和待批准区接口
            if type(settings.Params['port']) is int:   # 判断是否配置了端口
                url = "http://%s:%s%s" %(settings.Params['server'],settings.Params['port'],settings.Params['urls'][action_type])
            else:
                # 没有配置端口的情况
                url = "http://%s%s" %(settings.Params['server'],settings.Params['urls'][action_type])

            url =  self.__attach_token(url)    # __attach_token加上端口验证
            print('Connecting [%s], it may take a minute' % url)
            if method == "get":      # get请求
                args = ""
                for k,v in data.items():
                    args += "&%s=%s" %(k,v)   # 拼接出get请求参数
                args = args[1:]
                url_with_args = "%s?%s" %(url,args)   # 拼接出携带请求参数的请求url
                try:
                    # 打开一个url
                    req = urllib.request.urlopen(url_with_args ,timeout=settings.Params['request_timeout'])
                    # req_data = urllib.urlopen(req,timeout=settings.Params['request_timeout'])
                    # callback = req_data.read()
                    callback = req.read()
                    print("-->server response:",callback)
                    return callback
                except urllib.URLError as e:
                    sys.exit("\033[31;1m%s\033[0m"%e)
            elif method == "post":    # post请求
                try:
                    data_encode = urllib.parse.urlencode(data).encode()
                    req = urllib.request.urlopen(url=url,data=data_encode)
                    # res_data = urllib.urlopen(req,timeout=settings.Params['request_timeout'])
                    callback = req.read()
                    callback = json.loads(callback)
                    print("\033[31;1m[%s]:[%s]\033[0m response:\n%s" %(method,url,callback))
                    return callback
                except Exception as e:
                    sys.exit("\033[31;1m%s\033[0m"%e)
        else:
            raise KeyError


    #def __get_asset_id_by_sn(self,sn):
    #    return  self.__submit_data("get_asset_id_by_sn",{"sn":sn},"get")
    def load_asset_id(self,sn=None):
        asset_id_file = settings.Params['asset_id']   # 拿到资产id的文件名
        has_asset_id = False
        if os.path.isfile(asset_id_file):  # 判断文件是否存在
            asset_id = open(asset_id_file).read().strip()
            if asset_id.isdigit():  # 判断资产id是否是整数
                return  asset_id
            else:
                has_asset_id =  False
        else:
            has_asset_id =  False

    def __update_asset_id(self,new_asset_id):
        asset_id_file = settings.Params['asset_id']
        f = open(asset_id_file, "w", encoding='utf-8')
        f.write(str(new_asset_id))
        f.close()

    def report_asset(self):
        """发送资产数据"""
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        asset_id = self.load_asset_id(asset_data["sn"])   # 取到资产id
        if asset_id:    # 如果有资产id：reported to server before
            asset_data["asset_id"] = asset_id   # 在资产数据中加入asset_id
            post_url = "asset_report"
        else:           # 如果没有资产id：first time report to server
            '''report to another url,this will put the asset into approval waiting zone, when the asset is approved ,this request returns
            asset's ID'''
            asset_data["asset_id"] = None   # 资产数据中加入asset_id，且值设为None
            post_url = "asset_report_with_no_id"

        data = {"asset_data": json.dumps(asset_data)}
        response = self.__submit_data(post_url,data,method="post")  # 使用post方法提交数据
        if "asset_id" in response:
            self.__update_asset_id(response["asset_id"])

        self.log_record(response)

    def log_record(self, log, action_type=None):
        f = open(settings.Params["log_file"],"ab")
        if log is str:
            pass
        if type(log) is dict:
            if "info" in log:
                for msg in log["info"]:
                    log_format = "%s\tINFO\t%s\n" %(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),msg)
                    #print msg
                    f.write(log_format.encode())
            if "error" in log:
                for msg in log["error"]:
                    log_format = "%s\tERROR\t%s\n" %(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),msg)
                    f.write(log_format.encode())
            if "warning" in log:
                for msg in log["warning"]:
                    log_format = "%s\tWARNING\t%s\n" %(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),msg)
                    f.write(log_format.encode())

        f.close()