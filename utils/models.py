#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 
from  django.db import models

class BaseModel(models.Model):
    '''
    基类，公共字段
    '''
    create_time = models.DateTimeField('创建时间',auto_now_add=True)
    update_time = models.DateTimeField('更新时间',auto_now=True)
    is_delete = models.BooleanField('逻辑删除',default=False)

    class Meta:
        # 抽象类，用于继承，设置了abstract =True后，迁移的时候不创建表，注意：基类是不应该被创建成表的
        abstract =True