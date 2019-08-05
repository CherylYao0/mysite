from django.urls import path, re_path

from . import views

app_name = "verifications"

urlpatterns = [
    path('image_code/', views.image_code_view, name='image_code'),

]

# re_path(r'^image_codes/(?P<image_code_id>[\w-]+)/$', view=views.ImageCodeView.as_view(), name="image_code"),
# image_code_id为uuid格式
# path('image_codes/<uuid:image_code_id>/', views.ImageCode.as_view(), name='image_code'),