from django.urls import path
from . import views
# url的命名空间
app_name = 'myadmin'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('wait/', views.WaitView.as_view(), name='wait'),
    path('menus/', views.MenuListView.as_view(), name='menu_list'),
    path('menu/', views.MenuAddView.as_view(), name='menu_add'),
    path('menu/<int:menu_id>/', views.MenuUpdateView.as_view(), name='menu_manage'),
]