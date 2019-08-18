import logging

from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator
from django.db.models import F

from .models import Tag, News
from . import constants
from utils.res_code import json_response

logger = logging.getLogger('django')

def index(request):
    """
    新闻首页视图
    url: /
    :param request:
    :return:
    """
    # 新闻标签
    tags = Tag.objects.only('id', 'name').filter(is_delete =False)
    return render(request, 'news/index.html',
                  context={
                      'tags': tags
                  })


class NewsListView(View):
    """
    新闻列表视图
    url: /news/
    args: tag, page
    """
    def get(self, request):
        # 1、获取参数
        try:
            tag_id = int(request.GET.get('tag', 0))
        except Exception as e:
            logger.error('标签错误：\n{}'.format(e))
            tag_id = 0

        try:
            page = int(request.GET.get('page', 0))
        except Exception as e:
            logger.error('页码错误：\n{}'.format(e))
            page = 1
        # 使用only返回的是对象，所以传递到前端时需要迭代处理
        # news_queryset = News.objects.select_related('tag', 'author').only(
        #     'title', 'digest', 'image_url', 'update_time', 'tag__name', 'author__username')
        # values 返回字典
        # 2、获取查询集，不会去数据库 惰性
        # values返回的是字典，only返回的是对象；F方法的效果类似于as的效果select name as tag_name from tb_tag;
        news_queryset = News.objects.values('id', 'title', 'digest', 'image_url', 'update_time').annotate(tag_name=F('tag__name'), author=F('author__username'))
        # 3、过滤
        # if tag_id:
        #     news = news_queryset.filter(is_delete=False, tag_id=tag_id)
        # else:
        #     news = news_queryset.filter(is_delete=False)
        news = news_queryset.filter(is_delete=False, tag_id=tag_id) or news_queryset.filter(is_delete=False)
        # 4、分页
        paginator = Paginator(news, constants.PER_PAGE_NEWS_COUNT)

        # 获取页面数据
        # 方式一：news_info = paginator.page(page) 但是会报错，get_page可以容错
        news_info = paginator.get_page(page)
        # 5、返回数据
        data = {
            'total_pages': paginator.num_pages,
            'news': list(news_info) #news_info不是列表，但它可迭代
        }
        return json_response(data=data)