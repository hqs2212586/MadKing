# -*- coding:utf-8 -*-
__author__ = 'Qiushi Huang'


from assets import models
from django.db.models import Count
import random

class AssetDashboard(object):
    '''首页画图需要的数据都在这里生产'''
    def __init__(self,reqeust):
        self.requeset = reqeust
        self.asset_list = models.Asset.objects.all()
        self.data = {}