#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 
import re
from django import forms
from django_redis import get_redis_connection
from django.db.models import Q
from django.contrib.auth import login
from .models import Users
from verifications.constants import SMS_CODE_LENGTH
from verifications.forms import mobile_validator
from . import constants

class RegisterForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=20, min_length=5,
                               error_messages={
                                   'max_length': '用户名长度要小于20',
                                   'min_length': '用户名长度要大于4',
                                   'required': '用户名不能为空'
                               })
    password = forms.CharField(label='密码', max_length=20, min_length=6,
                               error_messages={
                                   'max_length': '密码长度要小于20',
                                   'min_length': '密码长度要大于5',
                                   'required': '用户名不能为空'
                               })
    password_repeat = forms.CharField(label='确认密码', max_length=20, min_length=6,
                                      error_messages={
                                          'max_length': '密码长度要小于20',
                                          'min_length': '密码长度要大于5',
                                          'required': '用户名不能为空'
                                      })
    mobile = forms.CharField(label='手机号码', max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={
                                 'max_length': '手机号码长度有误',
                                 'min_length': '手机号码长度有误',
                                 'required': '手机号码不能为空'
                             })
    sms_code = forms.CharField(label='短信验证码', max_length=SMS_CODE_LENGTH, min_length=SMS_CODE_LENGTH,
                               error_messages={
                                   'max_length': '短信验证码长度有误',
                                   'min_length': '短信验证码长度有误长度有误',
                                   'required': '短信验证码不能为空'
                               })

    def clean_username(self):
        """
        校验用户名
        :return:
        """
        username = self.cleaned_data.get('username')
        if Users.objects.filter(username=username).exists():
            return forms.ValidationError('用户名已存在！')
        return username

    def clean_mobile(self):
        """
        校验手机号
        :return:
        """
        mobile = self.cleaned_data.get('mobile')
        # 前面用了validators=[mobile_validator, ],所以这里不需要格式校验
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     raise forms.ValidationError('手机号码格式不正确')

        if Users.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError('手机号码已注册！')

        return mobile



    def clean(self):
        '''
            多个字段联合校验一般用clean
            单独校验，写多少校验多少，当我们需要详细的错误提醒信息的时候就用单字段校验，比如{'mobile':[]}
            而多字段校验一般是{'__all__',[]}

        联合校验，密码，和短信验证码
        :return:
        '''
        clean_data = super().clean()
        # 校验密码是否一致
        password = clean_data.get('password')
        password_repeat = clean_data.get('password_repeat')
        if password != password_repeat:
            raise forms.ValidationError('两次密码不一致！')

        # 校验短信验证码
        sms_code = clean_data.get('sms_code')
        moblie = clean_data.get('mobile')

        redis_conn = get_redis_connection(alias='verify_codes')
        real_code = redis_conn.get('sms_text_{}'.format(moblie))
        if (not real_code) or (real_code.decode('utf-8') != sms_code):
            raise forms.ValidationError('短信验证码错误!')

class LoginForm(forms.Form):
    account = forms.CharField(error_messages={'required':'账户不能为空'})

    password = forms.CharField(label='密码', max_length=20, min_length=6,
                               error_messages={
                                   'max_length': '密码长度要小于20',
                                   'min_length': '密码长度要大于5',
                                   'required': '用户名不能为空'
                               })

    remember = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request',None)
        super().__init__(*args, **kwargs)

    def clean_account(self):
        '''
        校验用户名
        :return:
        '''
        account = self.cleaned_data.get('account')
        if not re.match(r'^1[3-9]\d{9}$',account) and (len(account) < 5 or len(account) > 20):
            raise forms.ValidationError('用户账户格式不正确，请重新输入')
        # if re.match(r'^1[3-9]\d{9}$',account):
        #     pass
        # else:
        #     if len(account) < 5 or len(account) > 20:
        #         raise forms.ValidationError('用户账户格式不正确，请重新输入')
        return account

    def clean(self):
        '''
        校验用户名密码，并实现登录逻辑
        :return:
        '''
        clean_data = super().clean()

        account = clean_data.get('account')
        password = clean_data.get('password')
        remember = clean_data.get('remember')
        # 登录逻辑
        # 判断用户名密码是否匹配
        # 1、先找到这个用户
        # select * from tb_user where mobile=account or username=account;
        user_queryset = Users.objects.filter(Q(mobile=account)|Q(username=account))
        # 判断用户是否存在
        if user_queryset:
            # 2、校验这个密码是否匹配
            user = user_queryset.first()
            if user.check_password(password):
                # 是否免登陆
                if remember:
                    # 免登录14天
                    self.request.session.set_expiry(constants.USER_SESSION_EXPIRY)
                else:
                    # 关闭浏览器清除登录状态
                    self.request.session.set_expiry(0)
                # 登录
                login(self.request, user)
            else:
                raise forms.ValidationError('用户名密码错误！')
        else:
            raise forms.ValidationError('用户账户不存在，请重新输入！')
        return clean_data





















