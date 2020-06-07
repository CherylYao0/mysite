#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 

from haystack import indexes
from .models import News


class NewsIndex(indexes.SearchIndex, indexes.Indexable):
    """
    这个模型的作用类似django的模型，它告诉haystack哪些数据会被
    放进查询返回的模型对象中，以及通过哪些字段进行索引和查询
    """
    # 这字段必须这么写，用来告诉haystack和搜索引擎要索引哪些字段
    text = indexes.CharField(document=True, use_template=True)
    id = indexes.CharField(model_attr='id')  # News的id
    title = indexes.CharField(model_attr='title')
    digest = indexes.CharField(model_attr='digest')
    content = indexes.CharField(model_attr='content')
    image_url = indexes.CharField(model_attr='image_url')

    def get_model(self):
        """
        返回建立索引的模型
        :return:
        """
        return News

    def index_queryset(self, using=None):
        """
        返回要建立索引的数据查询集
        :param using:
        :return:
        """
        return self.get_model().objects.filter(is_delete=False)
