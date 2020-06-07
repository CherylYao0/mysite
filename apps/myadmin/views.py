from django.http import QueryDict
from django.shortcuts import render
from django.views import View
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .forms import MenuModelForm
from .models import Menu
from . import models
from utils.res_code import json_response, Code


# Create your views here.

class IndexView(View):
    """
    后台首页视图
    """

    def get(self, request):
        '''
        通过用户，通过权限，去获取这个列表
        :param request:
        :return:
        '''
        # menus = [
        #     {
        #         "name": "工作台",
        #         "url": "myadmin:home",
        #         "icon": "fa-desktop"
        #     },
        #     {
        #         "name": "新闻管理",
        #         "icon": "fa-newspaper-o",
        #         "children": [
        #             {
        #                 "name": "新闻标签管理",
        #                 "url": "myadmin:wait"
        #             }, {
        #                 "name": "新闻管理",
        #                 "url": "myadmin:wait"
        #             }, {
        #                 "name": "热门新闻管理",
        #                 "url": "myadmin:wait"
        #             }
        #         ]
        #     },
        #     {
        #         "name": "轮播图管理",
        #         "icon": "fa-picture-o",
        #         "url": "myadmin:home"
        #     },
        #     {
        #         "name": "文档管理",
        #         "icon": "fa-folder",
        #         "url": "myadmin:home"
        #     },
        #     {
        #         "name": "在线课堂",
        #         "icon": "fa-book",
        #         "children": [
        #             {
        #                 "name": "课程分类管理",
        #                 "url": "myadmin:wait"
        #             },
        #             {
        #                 "name": "课程管理",
        #                 "url": "myadmin:wait"
        #             },
        #             {
        #                 "name": "讲师管理",
        #                 "url": "myadmin:wait"
        #             }
        #         ]
        #     },
        #     {
        #         "name": "系统设置",
        #         "icon": "fa-cogs",
        #         "children": [
        #             {
        #                 "name": "权限管理",
        #                 "url": "myadmin:wait"
        #             },
        #             {
        #                 "name": "用户管理",
        #                 "url": "myadmin:wait"
        #             },
        #             {
        #                 "name": "菜单管理",
        #                 "url": "myadmin:menu_list"
        #             },
        #             {
        #                 "name": "个人信息",
        #                 "url": "myadmin:wait"
        #             }
        #         ]
        #     }
        #
        # ]

        # 1、拿到所有的可用、可见菜单，一级菜单
        objs = Menu.objects.only('name', 'url', 'icon', 'permission__codename',
                                 'permission__content_type__app_label').select_related(
            'permission__content_type').filter(is_delete=False, is_visible=True, parent=None)
        # 2、过滤用户拥有权限的菜单，request.user就是当前登录用户
        has_permissions = request.user.get_all_permissions()
        # 3、构造数据结构
        menus = []
        for menu in objs:
            if '%s.%s' % (menu.permission.content_type.app_label, menu.permission.codename) in has_permissions:
                temp = {
                    'name': menu.name,
                    'icon': menu.icon
                }
                # 检查是否有可用，可见的子菜单
                children = menu.children.filter(is_delete=False, is_visible=True)
                if children:
                    temp['children'] = []
                    for child in children:
                        if '%s.%s' % (
                                child.permission.content_type.app_label, child.permission.codename) in has_permissions:
                            temp['children'].append({
                                'name': child.name,
                                'url': child.url
                            })
                else:
                    if not menu.url:
                        continue
                    temp['url'] = menu.url
                menus.append(temp)
        return render(request, 'myadmin/index.html', context={'menus': menus})


class HomeView(View):
    """
    工作台视图
    """

    def get(self, request):
        return render(request, 'myadmin/home.html')


class WaitView(View):
    """
    未上线功能提示
    """

    def get(self, request):
        return render(request, 'myadmin/wait.html')


class MenuListView(View):
    """
    菜单列表视图
    url:/admin/menus/
    """

    def get(self, request):
        # 拿到所有的一级菜单
        # 当parent=None就表示该菜单是一级菜单
        menus = models.Menu.objects.only('name', 'url', 'icon', 'is_visible', 'order', 'codename', 'is_delete').filter(
            parent=None)

        return render(request, 'myadmin/menu/menu_list.html', context={'menus': menus})


class MenuAddView(View):
    """
    添加菜单视图
    url:/admin/menu/
    """

    def get(self, request):

        form = MenuModelForm()
        return render(request, 'myadmin/menu/add_menu.html', context={'form': form})

    def post(self, request):
        form = MenuModelForm(request.POST)

        if form.is_valid():
            # 创建菜单
            new_menu = form.save()
            # 菜单的权限对象
            content_type = ContentType.objects.filter(app_label='myadmin', model='menu').first()
            # permission需要content_type
            permission = Permission.objects.create(name=new_menu.name, content_type=content_type,
                                                   codename=new_menu.codename)
            new_menu.permission = permission
            new_menu.save(update_fields=['permission'])
            return json_response(errmsg='菜单添加成功！')
        else:
            return render(request, 'myadmin/menu/add_menu.html', context={'form': form})


class MenuUpdateView(View):
    """
    菜单管理视图
    url:/admin/menu/<int:menu_id>/
    """

    def get(self, request, menu_id):
        menu = Menu.objects.filter(id=menu_id).first()
        # 创建form的时候给个instance，再去渲染的时候把它传给context，那么Django会自动帮你把对象里的内容渲染出来
        form = MenuModelForm(instance=menu)
        return render(request, 'myadmin/menu/update_menu.html', context={'form': form})

    def delete(self, request, menu_id):
        '''
        只有写delete方法，delete请求才会过来
        注意：这里是真删除！会删除数据库数据，软删除放到修改里面，因为菜单的数据并不是很重要，这是整个菜单管理里面唯一一个真删除
        :param request:
        :param menu_id:
        :return:
        '''
        menu = Menu.objects.filter(id=menu_id).only('name')
        if menu:
            menu = menu[0]  # 相当于 menu.first()
            # 看看是否是父菜单
            if menu.children.filter(is_delete=False).exists():
                return json_response(errno=Code.DATAERR, errmsg='父菜单不能删除！')
            menu.permission.delete()
            # 不需要 menu.delete() 这一步是因为permission改为了级联删除，删除了permission， menu也会被删掉
            # menu.delete()
            return json_response(errmsg='删除菜单：%s成功' % menu.name)
        else:
            return json_response(errno=Code.NODATA, errmsg='菜单不存在！')

    def put(self, request, menu_id):
        menu = Menu.objects.filter(id=menu_id).first()
        if not menu:
            return json_response(errno=Code.NODATA, errmsg='菜单不存在')
        # 获取put请求的参数
        put_data = QueryDict(request.body)
        # 必须传递instance=menu，绑定表单
        form = MenuModelForm(put_data, instance=menu)
        if form.is_valid():
            # 这样写是拿到新的 menu 对象
            obj = form.save()
            # 检查修改了的字段是否和权限有关，如果有关就要修改权限
            flag = False
            # 通过 form.changed_data 拿到被修改的字段列表
            if 'name' in form.changed_data:
                obj.permission.name = obj.name
                flag = True
            if 'codename' in form.changed_data:
                obj.permission.codename = obj.codename
                flag = True
            if flag:
                obj.permission.save()
            return json_response(errmsg='菜单修改成功！')
        else:
            return render(request, 'myadmin/menu/update_menu.html', context={'form': form})

class UserListView(View):
    """
    用户列表视图
    """

    def get(self, request):
        user_queryset = Users.objects.only('username', 'is_active', 'mobile', 'is_staff', 'is_superuser')
        groups = Group.objects.only('name').all()
        query_dict = {}
        # 检索
        groups__id = request.GET.get('group')
        if groups__id:
            try:
                group_id = int(groups__id)
                query_dict['groups__id'] = groups__id
            except Exception as e:
                pass

        is_staff = request.GET.get('is_staff')
        if is_staff == '0':
            query_dict['is_staff'] = False
        if is_staff == '1':
            query_dict['is_staff'] = True

        is_superuser = request.GET.get('is_superuser')
        if is_superuser == '0':
            query_dict['is_superuser'] = False
        if is_superuser == '1':
            query_dict['is_superuser'] = True

        username = request.GET.get('username')

        if username:
            query_dict['username'] = username

        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            page = 1

        paginater = Paginator(user_queryset.filter(**query_dict), 2)

        users = paginater.get_page(page)
        context = {
            'users': users,
            'groups': groups
        }
        context.update(query_dict)
        return render(request, 'myadmin/user/user_list.html', context=context)