#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 
from django.urls import path
from . import views

app_name = 'doc'

urlpatterns = [
    path('download/', views.index, name='index'),
    path('docs/', views.DocListView.as_view(), name='doc_list'),
    path('dload/', views.DownloadView.as_view(), name='doc_list'),
]