from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as _UserManager


class UserManager(_UserManager):
    """
    自定义管理器，用来修改使用createsuperuser命令创建用户必须提供email的行为
    这里是为了让email成为非必需参数
    """

    def create_superuser(self, username, password, email=None, **extra_fields):
        super(UserManager, self).create_superuser(username=username,
                                                  password=password, email=email, **extra_fields)


class Users(AbstractUser):
    """
    自定义的User模型，添加mobile，email_active字段
    """
    # 模型管理器
    objects = UserManager()

    # 通过createsuperuser 这个命令创建用户时，需要的字段
    REQUIRED_FIELDS = ['mobile']

    # help_text在api接口文档中会用到，verbose_name在admin站点中会用到
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号", help_text='手机号',
                              error_messages={'unique': "此手机号已注册"}  # 指定报错的中文信息
                              )
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = "tb_user"   # 指明数据库表名
        verbose_name = "用户"    # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):  # 打印对象时调用
        return self.username