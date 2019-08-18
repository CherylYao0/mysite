#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 

from django import forms
from django.core.validators import RegexValidator
from django_redis import get_redis_connection
from users.models import Users

# 创建手机号的正则校验器
mobile_validator = RegexValidator(r'^1[3-9]\d{9}$', '手机号码格式不正确')


class CheckImageForm(forms.Form):
    '''
    校验图形验证码
        1、校验手机号码
        2、校验图形验证码
        3、校验是否在60s内有发送记录
    '''

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    # mobile，captcha是必须和前端ajax传过来的参数key一一对应的
    mobile = forms.CharField(max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={
                                 'max_length': '手机长度有误',
                                 'min_length': '手机长度有误',
                                 'required': '手机号不能为空'
                             })

    captcha = forms.CharField(max_length=4, min_length=4,
                              error_messages={
                                  'max_length': '图形验证码长度有误',
                                  'min_length': '图形验证码长度有误',
                                  'required': '图形验证码不能为空'
                              })
    def clean(self):
        clean_data = super().clean()
        mobile = clean_data.get('mobile')
        captcha = clean_data.get('captcha')
        # 如果前面的字段校验失败，mobile captcha就是none，就不需要往下进行了
        if mobile and captcha:
            # 1.校验图片验证码
            # 获取session中保存的验证码，和用户填入的进行比对
            image_code = self.request.session.get('image_code')
            if not image_code:
                raise forms.ValidationError('图片验证码失效！')
            if image_code.upper() != captcha.upper():
                raise forms.ValidationError('图片验证码校验失败！')

            # 2.校验是否在60秒内已发送过短信
            redis_conn = get_redis_connection(alias='verify_codes')
            if redis_conn.get('sms_flag_{}'.format(mobile)):
                raise forms.ValidationError('获取短信验证码过于频繁')

            # 3.校验手机号码是否已注册
            if Users.objects.filter(mobile=mobile).count():
            # 或 if Users.objects.filter(mobile=mobile).exists():
                raise forms.ValidationError('手机号已注册，请重新输入')

        return clean_data

    '''
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    mobile = forms.CharField(max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={
                                 'max_length': '手机长度有误',
                                 'min_length': '手机长度有误',
                                 'required': '手机号不能为空'
                             })

    captcha = forms.CharField(max_length=4, min_length=4,
                              error_messages={
                                  'max_length': '验证码长度有误',
                                  'min_length': '图片验证码长度有误',
                                  'required': '图片验证码不能为空'
                              })

    def clean(self):
        clean_data = super().clean()
        mobile = clean_data.get('mobile')
        captcha = clean_data.get('captcha')
        # 1.校验图片验证码
        image_code = self.request.session.get('image_code')
        if (not image_code) or (image_code.upper() != captcha.upper()):
            raise forms.ValidationError('图片验证码校验失败！')

        # 2.校验是否在60秒内已发送过短信
        redis_conn = get_redis_connection(alias='verify_code')
        if redis_conn.get('sms_flag_{}'.format(mobile)):
            raise forms.ValidationError('获取短信验证码过于频繁')

        # 3.校验手机号码是否已注册
        if User.objects.filter(mobile=mobile).count():
            raise forms.ValidationError('手机号已注册，请重新输入')
    '''
