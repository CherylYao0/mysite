from django.db import models
from django.contrib.auth.models import Permission
from utils.models import BaseModel

class Menu(BaseModel):
    name = models.CharField('菜单名', max_length=48, help_text='菜单名', unique=True)
    url = models.CharField('路由名称', max_length=256, null=True, blank=True, help_text='url')

    # related_name 当我们通过反向查询的时候，可以通过children这个属性连到我们的菜单；
    # 比如通过父菜单想查询子菜单的时候，就可以通过父菜单的children查到
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父菜单')
    order = models.SmallIntegerField('排序', default=0)
    permission = models.OneToOneField(Permission, on_delete=models.CASCADE, null=True)
    icon = models.CharField('图标', max_length=48, default='fa-link')

    codename = models.CharField('权限码', max_length=48, help_text='权限码', unique=True)
    is_visible = models.BooleanField('是否可见', default=False)

    class Meta:
        ordering = ['-order']
        db_table = 'tb_menu'
        verbose_name = '菜单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
