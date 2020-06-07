#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HuangManyao

from django import forms
from .models import Menu


class MenuModelForm(forms.ModelForm):
    '''
    模型表单
    '''
    # 重新定义父菜单
    parent = forms.ModelChoiceField(queryset=None, required=False, help_text='父菜单')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 想让它展示什么，就写什么样的queryset（添加菜单时modal里面parent的下拉框）
        self.fields['parent'].queryset = Menu.objects.filter(is_delete=False, is_visible=True, parent=None)

    class Meta:
        model = Menu
        fields = ['name', 'url', 'order', 'parent', 'icon', 'codename', 'is_visible']
