from django.urls import path
from . import views
# url的命名空间
app_name = 'news'

urlpatterns = [
    path('', views.index, name='index'),    # 将这条路由命名为index
    path('news/', views.NewsListView.as_view(), name='news_list')
]