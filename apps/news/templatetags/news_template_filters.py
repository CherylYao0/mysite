#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 
from django import template

register = template.Library()


@register.filter
def page_bar(page):
    '''
    :param page: 当前页，从前端传过来的
    :return:
    '''
    page_list = []
    # 当前页左边的逻辑
    if page.number != 1:
        page_list.append(1)
    if page.number - 3 > 1:
        page_list.append('...')
    if page.number - 2 > 1:
        page_list.append(page.number - 2)
    if page.number - 1 > 1:
        page_list.append(page.number - 1)

    page_list.append(page.number)

    # 当前页右边的逻辑
    # page.paginator.num_pages 总页数
    if page.paginator.num_pages > page.number + 1:
        page_list.append(page.number + 1)
    if page.paginator.num_pages > page.number + 2:
        page_list.append(page.number + 2)
    if page.paginator.num_pages > page.number + 3:
        page_list.append('...')
    if page.paginator.num_pages != page.number:
        page_list.append(page.paginator.num_pages)
    return page_list