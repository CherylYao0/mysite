#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao
import json,datetime
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

class Code:
    OK = "0"
    DBERR = "4001"
    NODATA = "4002"
    DATAEXIST = "4003"
    DATAERR = "4004"
    METHERR = "4005"
    SMSERROR = "4006"
    SMSFAIL = "4007"

    SESSIONERR = "4101"
    LOGINERR = "4102"
    PARAMERR = "4103"
    USERERR = "4104"
    ROLEERR = "4105"
    PWDERR = "4106"

    SERVERERR = "4500"
    UNKOWNERR = "4501"


error_map = {
    Code.OK: "成功",
    Code.DBERR: "数据库查询错误",
    Code.NODATA: "无数据",
    Code.DATAEXIST: "数据已存在",
    Code.DATAERR: "数据错误",
    Code.METHERR: "方法错误",
    Code.SMSERROR: "发送短信验证码异常",
    Code.SMSFAIL: "发送短信验证码失败",

    Code.SESSIONERR: "用户未登录",
    Code.LOGINERR: "用户登录失败",
    Code.PARAMERR: "参数错误",
    Code.USERERR: "用户不存在或未激活",
    Code.ROLEERR: "用户身份错误",
    Code.PWDERR: "密码错误",

    Code.SERVERERR: "内部错误",
    Code.UNKOWNERR: "未知错误",
}




# json编码器
# 自定义序列化器，处理时间字段.  因为json默认不支持datetime类型数据，所以自定义json编码器
class MyJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            # o.astimezone() 意思是转化为当前时区
            return o.astimezone().strftime('%Y-%m-%d %H:%M:%S')  # 转换为本地时间

def json_response(errno=Code.OK,errmsg='',data=None,kwargs=None):
    json_dict = {
        'errno': errno,
        'errmsg': errmsg,
        'data': data
    }
    if kwargs and isinstance(kwargs, dict):
        json_dict.update(kwargs)

    return JsonResponse(json_dict,encoder=MyJSONEncoder)