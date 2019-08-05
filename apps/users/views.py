from django.shortcuts import render

# Create your views here.
from django.views import View

class LoginView(View):

    def get(self,request):
        return render(request,'users/login.html')

class RegisterView(View):
    '''
    注册页面
    url: /users/register
    '''
    def get(self,request):
        return render(request,'users/register.html')