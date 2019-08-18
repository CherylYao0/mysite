from django.shortcuts import render,redirect,reverse

# Create your views here.
from django.views import View
from django.contrib.auth import logout
from .forms import RegisterForm,LoginForm
from .models import Users
from utils.res_code import json_response,Code

class LoginView(View):

    def get(self, request):
        return render(request, 'users/login.html')

    def post(self,request):
        '''
        1、先校验
        2、再登陆
        :param request:
        :return:
        '''
        form = LoginForm(request.POST,request=request)
        if form.is_valid():
            return json_response(errmsg='恭喜登陆成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.values():
                err_msg_list.append(item[0])
            err_msg_str = '/'.join(err_msg_list)
            return json_response(errno=Code.PARAMERR, errmsg=err_msg_str)

class RegisterView(View):
    '''
    注册页面
    url: /users/register
    '''

    def get(self, request):
        return render(request, 'users/register.html')

    def post(self, request):
        '''
        form
        :param request:
        :return:
        '''
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 2.创建数据
            username = request.POST.get('username')
            password = request.POST.get('password')
            mobile = form.cleaned_data.get('mobile')
            Users.objects.create_user(username=username, password=password, mobile=mobile)
            return json_response(errmsg='恭喜你，注册成功！')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.values():
                err_msg_list.append(item[0])
            err_msg_str = '/'.join(err_msg_list)

            return json_response(errno=Code.PARAMERR, errmsg=err_msg_str)


class LogoutView(View):
    """
    登出视图
    """

    def get(self, request):
        logout(request)
        return redirect(reverse('users:login'))