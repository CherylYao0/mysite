# Create your views here.
import logging
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse
logger = logging.getLogger('django')

from utils.captcha.captcha import captcha
# 安装图片验证码所需要的 Pillow 模块
# pip install Pillow
from . import constants
from users.models import Users

def image_code_view(request):
    '''
    生成验证码
    url:/image_code/
    :param request:
    :return:
    '''
    # 1、生成一个验证码--->随机生成字符串，然后生成图片
    text,image = captcha.generate_captcha()
    # 2、在后端保存验证码，为什么要保存，是为了等下拿来校验
    # 怎么保证会话的连续性，两个请求连接在一起-----> 保存在session中
    request.session['image_code'] = text
    # 定义过期时间，
    request.session.set_expiry(constants.IMAGE_CODE_EXPIRES)
    # 3、记录一个日志
    logger.info('Image code:{}'.format(text))
    # 4、返回验证码图片
    return HttpResponse(content=image,content_type="image/jpg")




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