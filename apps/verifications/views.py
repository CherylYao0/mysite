# Create your views here.
import logging,random
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
from django.views import View

logger = logging.getLogger('django')

from utils.captcha.captcha import captcha
from utils.res_code import json_response,Code,error_map
from utils.yuntongxun.sms import CCP

# 安装图片验证码所需要的 Pillow 模块
# pip install Pillow
from . import constants
from users.models import Users
from .forms import CheckImageForm

def image_code_view(request):
    '''
    生成验证码
    url:/image_code/
    :param request:
    :return:
    '''
    # 1、生成一个验证码--->随机生成字符串，然后生成图片
    text, image = captcha.generate_captcha()
    # 2、在后端保存验证码，为什么要保存，是为了等下拿来校验
    # 怎么保证会话的连续性，两个请求连接在一起-----> 保存在session中
    request.session['image_code'] = text
    # 定义过期时间，
    request.session.set_expiry(constants.IMAGE_CODE_EXPIRES)
    # 3、记录一个日志
    logger.info('Image code:{}'.format(text))
    # 4、返回验证码图片
    return HttpResponse(content=image, content_type="image/jpg")


# # 导入日志器
#
#
#
# class ImageCode(View):
#     """
#     define image verification view
#     # /image_codes/<uuid:image_code_id>/
#     """
#
#     def get(self, request, image_code_id):
#         text, image = captcha.generate_captcha()
#
#         # 确保settings.py文件中有配置redis CACHE
#         # Redis原生指令参考 http://redisdoc.com/index.html
#         # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
#         con_redis = get_redis_connection(alias='verify_codes')
#         img_key = "img_{}".format(image_code_id)
#         # 将图片验证码的key和验证码文本保存到redis中，并设置过期时间
#         con_redis.setex(img_key, constants.IMAGE_CODE_EXPIRES, text)
#         logger.info("Image code: {}".format(text))
#
#         return HttpResponse(content=image, content_type="image/jpg")


def check_username_view(request, username):
    '''
    校验用户名
    :param request:
    :param username:
    :return:
    '''
    # data = {
    #     "errno": "0",
    #     "errmsg": "OK",
    #     "data": {
    #         "username": username,  # 查询的用户名
    #         "count": Users.objects.filter(username=username).count()  # 用户名查询的数量
    #     }
    # }
    data = {
        "username": username,  # 查询的用户名
        "count": Users.objects.filter(username=username).count()  # 用户名查询的数量
    }
    return json_response(data=data)


def check_mobile_view(request, mobile):
    '''
    校验手机号是否存在
    url:/moblie/(?P<moblie>1[3-9]\d{9})/
    :param request:
    :param mobile:
    :return:
    '''
    # data = {
    #     "errno": "0",
    #     "errmsg": "OK",
    #     "data": {
    #         "mobile": mobile,  # 查询的手机号
    #         "count": Users.objects.filter(mobile=mobile).count()  # 手机号查询的数量
    #     }
    # }

    data = {
        "mobile": mobile,  # 查询的手机号
        "count": Users.objects.filter(mobile=mobile).count()  # 手机号查询的数量
    }
    return json_response(data=data)


class SmsCodeView(View):
    '''
    发送短信验证码
    url:/sms_code/
    '''
    def post(self,request):
        '''

        - 发送短信
        - 保存这个短信验证码（保存在哪里？）
        - 保存发送记录
        :param request:
        :return:
        '''
        form = CheckImageForm(request.POST,request=request)
        if form.is_valid():
            # success
            # 获取手机号码
            mobile = form.cleaned_data.get('mobile')
            # 生成短信验证码
            sms_code = ''.join([random.choice('0123456789') for _ in range(constants.SMS_CODE_LENGTH)])
            # 发送短信验证码，调用接口
            # ..........
            # 保存发送记录
            # logger.info('发送短信验证码[正常][mobile: %s sms_code: %s]' % (mobile,sms_code))
            ccp = CCP()
            try:
                res = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_EXPIRES], "1")
                if res == 0:
                    logger.info('发送短信验证码[正常][mobile: %s sms_code: %s]' % (mobile, sms_code))
                else:
                    logger.error('发送短信验证码[失败][moblie: %s sms_code: %s]' % (mobile, sms_code))
                    return json_response(errno=Code.SMSFAIL, errmsg=error_map[Code.SMSFAIL])
            except Exception as e:
                logger.error('发送短信验证码[异常][mobile: %s message: %s]' % (mobile, e))
                return json_response(errno=Code.SMSERROR, errmsg=error_map[Code.SMSERROR])
            # 保存这个验证码 这里有个时限的问题
            # 两种方案：1、session  2、redis （不保存在MySQL是因为MySQL效率太低）
            # 但session的时限是统一设置的，这里如果重新设置时限，会把前面的session覆盖，因此排除session方案，用redis保存验证码
            # request.session['sms_code'] = sms_code
            # request.session.set_expiry
            # 60秒记录
            # 5分钟有效
            # 创建短信验证码发送记录的key
            sms_flag_key = 'sms_flag_{}'.format(mobile)
            # 创建短信验证码内容的key
            sms_text_key = 'sms_text_{}'.format(mobile)
            redis_coon = get_redis_connection(alias='verify_codes')
            # 创建一个管道
            pl = redis_coon.pipeline()
            try:
                pl.setex(sms_flag_key,constants.SMS_CODE_INTERVAL,1)
                pl.setex(sms_text_key,constants.SMS_CODE_EXPIRES * 60,sms_code)
                # 让管道通知redis执行命令
                pl.execute()
                return json_response(errmsg='短信验证码发送成功')
            except Exception as e:
                logger.error('redis 执行异常, {}'.format(e))
                return json_response(errno=Code.UNKOWNERR,errmsg=error_map[Code.UNKOWNERR])
        else:
            # fail
            # 将表单的报错信息进行拼接
            err_msg_list = []
            for item in form.errors.values():
                # item是一个列表，
                err_msg_list.append(item[0])
            err_msg_str = '/'.join(err_msg_list)
            return json_response(errno=Code.PARAMERR,errmsg=err_msg_str)