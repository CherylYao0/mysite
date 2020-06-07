#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao 
from django.template import Library
from django.shortcuts import reverse

register = Library()


@register.simple_tag()
def add_class(field, class_str):
    return field.as_widget(attrs={'class': class_str})

@register.simple_tag()
def my_url(pattern,*args):
    try:
        url = reverse(pattern,*args)
    except Exception as e:
        url = reverse('myadmin:wait')
    return url
