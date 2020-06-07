
from django.shortcuts import render, Http404
from django.views import View

from .models import Course

class IndexView(View):

    """
    在线课程首页，视频列表页面
    url:/course/
    """
    def get(self,request):
        courses = Course.objects.only('title', 'cover_url', 'teacher__title', 'teacher__name').filter(
            is_delete=False).select_related(
            'teacher')
        return render(request, 'course/course.html', context={'courses': courses})


class CourseDetailView(View):
    """
    课程详情视图
    url:/course/<int:course_id>/
    """

    def get(self, request, course_id):
        course = Course.objects.only('title', 'cover_url', 'video_url', 'profile', 'outline', 'teacher__name',
                                            'teacher__photo', 'teacher__title', 'teacher__profile').select_related(
            'teacher').filter(is_delete=False, id=course_id).first()

        if course:

            return render(request, 'course/course_detail.html', context={'course': course})
        else:
            return Http404('此课程不存在')