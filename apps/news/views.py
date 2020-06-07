import logging

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseNotFound
from haystack.generic_views import SearchView
from .models import Tag, News, HotNews, Comments, Banner
from django.conf import settings
from . import constants
from utils.res_code import json_response,Code,error_map

logger = logging.getLogger('django')


def index(request):
    """
    新闻首页视图
    url: /
    :param request:
    :return:
    """
    # 新闻标签
    tags = Tag.objects.only('id', 'name').filter(is_delete=False)
    # 热门新闻
    # 加了select_related('news')
    hot_news = HotNews.objects.select_related('news').only('news__title', 'news__image_url', 'news__id').filter(
        is_delete=False).order_by('priority', '-news__clicks')[:constants.SHOW_HOTNEWS_COUNT]
    hot_news = HotNews.objects.only('news__title', 'news__image_url', 'news__id').filter(is_delete=False).order_by(
        'priority', '-news__clicks')[:constants.SHOW_HOTNEWS_COUNT]
    return render(request, 'news/index.html',
                  context={
                      'tags': tags,
                      'hot_news': hot_news,
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
        # 2、获取查询集，不会去数据库查询数据， 这是一个惰性操作，你不去获取它的值，它不会去操作数据库，filter也不会
        # values返回的是字典，only返回的是对象；F方法的效果类似于as的效果select name as tag_name from tb_tag;
        news_queryset = News.objects.values('id', 'title', 'digest', 'image_url', 'update_time').annotate(
            tag_name=F('tag__name'), author=F('author__username'))
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
            'news': list(news_info)  # news_info不是列表，但它可迭代
        }
        return json_response(data=data)


# 在news目录下views.py中创建如下视图
class NewsBannerView(View):
    """
    轮播图视图
    url:/news/banners/
    """

    def get(self, request):
        banners = Banner.objects.values('image_url', 'news_id').annotate(
            news_title=F('news__title')
        ).filter(is_delete=False)[:constants.SHOW_BANNER_COUNT]
        data = {
            'banners': list(banners)
        }
        return json_response(data=data)


class NewsDetailView(View):
    '''
    新闻详情视图
    url: /news/<int:news_id>/
    '''

    def get(self, request, news_id):
        # 1、校验是否存在
        # 2、获取数据
        # news = News.objects.select_related('tag','author').only('title','content','update_time','tag__name','author__username').filter(is_delete=False,id=news_id).first()
        # # 3、展示
        # if news:
        #     return render(request,'news/news_detail.html',context={'news':news})
        # else:
        #     return HttpResponseNotFound('<h1>Page Not Found</h1>')
        news_queryset = News.objects.select_related('tag', 'author').only(
            'title', 'content', 'update_time', 'tag__name', 'author__username')
        news = get_object_or_404(news_queryset, is_delete=False, id=news_id)
        # 获取评论
        comments = Comments.objects.select_related('author', 'parent__author').only(
            'content', 'author__username', 'update_time', 'parent__author__username', 'parent__content','parent__update_time'
        ).filter(is_delete=False, news_id=news_id)
        print(comments)
        return render(request, 'news/news_detail.html', context={
            'news': news,
            'comments': comments,
        })

class NewsCommentView(View):
    '''
    添加评论视图
    url: /news/<int:news_id>/comment/
    '''
    def post(self,request,news_id):
        # 是否登陆
        if not request.user.is_authenticated:
            return json_response(errno=Code.SESSIONERR,errmsg=error_map[Code.SESSIONERR])
        # 新闻是否存在
        if not  News.objects.filter(is_delete=False,id=news_id).exists():
            return json_response(errno=Code.PARAMERR,errmsg='新闻不存在')

        # 判断内容
        content = request.POST.get('content')
        if not content:
            return json_response(errno=Code.PARAMERR,errmsg='评论内容不能为空')
        # 父id是否正常
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_id = int(parent_id)
                if not Comments.objects.filter(is_delete=False,id=parent_id,news_id=news_id).exists():
                    return json_response(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
            except Exception as e:
                logger.info('前端传递过来的parent_id异常\n{}'.format(e))
                return json_response(errno=Code.PARAMERR, errmsg='未知异常')

        new_comment = Comments()
        new_comment.content = content
        new_comment.news_id = news_id
        new_comment.author = request.user
        if parent_id:
            new_comment.parent_id = parent_id
        # new_comment.parent_id = parent_id if parent_id else None
        new_comment.save()

        return json_response(data=new_comment.to_dict_data())


class NewsSearchView(SearchView):
    """
    新闻搜索视图
    url:/news/search/
    """
    # 配置搜索模板文件,这里必须要配置，否则return super().get(request, *args, **kwargs)找不到template_name
    template_name = 'news/search.html'

    # 重写get请求，如果请求参数q为空，返回模型News的热门新闻数据
    # 否则根据参数q搜索相关数据
    def get(self, request, *args, **kwargs):
        # 1、获取查询参数
        query = request.GET.get('q')
        if not query:
            # 2、如果没有查询参数
            # 返回热门新闻
            hot_news = HotNews.objects.select_related('news__tag').only('news__title', 'news__image_url', 'news_id','news__tag__name').filter(is_delete=False).order_by('priority', '-news__clicks')
            paginator = Paginator(hot_news, settings.HAYSTACK_SEARCH_RESULTS_PER_PAGE)
            try:
                page = paginator.get_page(int(request.GET.get('page')))
            except Exception as e:
                page = paginator.get_page(1)

            return render(request, self.template_name, context={
                'page': page,
                'query': query
            })
        else:
            # 3、如果有怎么办
            # 搜索
            # super().get(request, *args, **kwargs)传的page是page_obj
            return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        在context中添加page变量
        让super().get(request, *args, **kwargs)中传参page_obj和如果没有查询参数时传的page统一
        :param args:
        :param kwargs:
        :return:
        """
        context = super().get_context_data(*args, **kwargs)
        if context['page_obj']:
            context['page'] = context['page_obj']
        return context