from django.db import models

# Create your models here.
from django.db import models

from utils.models import BaseModel


class Teacher(BaseModel):
    name = models.CharField('讲师姓名', max_length=150, help_text='讲师姓名')
    title = models.CharField('职称', max_length=150, help_text='职称')
    profile = models.TextField('简介', help_text='简介')
    photo = models.URLField('头像url', default='', help_text='头像url')

    class Meta:
        db_table = 'tb_teachers'
        verbose_name = '讲师'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class CourseCategory(BaseModel):
    name = models.CharField('课程分类名', max_length=100, help_text='课程分类名')

    class Meta:
        db_table = 'tb_course_category'
        verbose_name = '课程分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Course(BaseModel):
    title = models.CharField('课程名', max_length=150, help_text='课程名')
    cover_url = models.URLField('封面url', help_text='封面url')
    video_url = models.URLField('课程视频url', help_text='课程视频url')
    duration = models.DurationField('课程时长', help_text='课程时长')
    profile = models.TextField('课程简介', null=True, blank=True, help_text='课程简介')
    outline = models.TextField('课程大纲', null=True, blank=True, help_text='课程大纲')
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'tb_course'
        verbose_name = '课程'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title