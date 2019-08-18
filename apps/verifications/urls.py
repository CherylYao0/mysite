from django.urls import path, re_path

from . import views

app_name = "verifications"

urlpatterns = [
    path('image_code/', views.image_code_view, name='image_code'),
    re_path('username/(?P<username>\w{5,20})',views.check_username_view,name="check_username"),
    re_path('mobile/(?P<mobile>1[3-9]\d{9})/', views.check_mobile_view, name='check_mobile'),
    path('sms_code/',views.SmsCodeView.as_view(),name='sms_code'),
]

# re_path(r'^image_codes/(?P<image_code_id>[\w-]+)/$', view=views.ImageCodeView.as_view(), name="image_code"),
# image_code_id为uuid格式
# path('image_codes/<uuid:image_code_id>/', views.ImageCode.as_view(), name='image_code'),