# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'

import os


BaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Params = {
    "server": "192.168.31.28",
    "port":8000,
    'request_timeout':30,
    "urls":{
        "asset_report_with_no_id":"/asset/report/asset_with_no_asset_id/",  # 新资产批准区接口
        "asset_report":"/asset/report/",   # 正式资产表接口
    },
    'asset_id': '%s/var/.asset_id' % BaseDir,  # 本机收集的数据保存在本地隐藏文件中
    'log_file': '%s/logs/run_log' % BaseDir,

    'auth':{
        'user':'lijie3721@126.com',
        'token': 'abc'
    },
}