import logging
from django.shortcuts import render,Http404
from django.utils.encoding import escape_uri_path
from django.views import View
from django.core.paginator import Paginator
from django.http import FileResponse
# Create your views here.
from .models import Doc
from . import constants
from utils.res_code import json_response

logger = logging.getLogger('django')

def index(request):
    '''
    :param request:
    :return: 文档下载页面
    '''
    return render(request, 'doc/docDownload.html')



class DocListView(View):
    def get(self, request):
        # 1.拿到所有文档
        docs = Doc.objects.values('file_url', 'file_name', 'title', 'desc', 'image_url').filter(is_delete=False)
        # 2.分页
        paginator = Paginator(docs, constants.PER_PAGE_DOC_COUNT)

        try:
            page = paginator.get_page(int(request.GET.get('page')))
        except Exception as e:
            page = paginator.get_page(1)
        # 3、序列化
        data = {
            'total_page': paginator.num_pages,
            'docs': list(page)
        }
        # 4、返回json响应
        return json_response(data=data)



class DownloadView(View):
    '''
    # 文件下载视图
    '''
    def get(self, request, doc_id):

        # file_fb = makefile()  # 生成文件流
        # 生成一个文件流（在内存中，以IO流的形式存在，像一个文件句柄一样，不是以一个文件的形式存在）
        file_fb = open('/home/pyvip/code/mysite/media/django项目班_英语单词.jpg','rb')
        try:
            res = FileResponse(file_fb) # 括号里只能写文件句柄
        except Exception as e:
            logger.info("获取文档内容出现异常：\n{}".format(e))
            raise Http404("文档下载异常！")

        ex_name = 'xls'  # 文件后缀，表明文件类型
        # https://stackoverflow.com/questions/23714383/what-are-all-the-possible-values-for-http-content-type-header
        # http://www.iana.org/assignments/media-types/media-types.xhtml#image
        if not ex_name:
            raise Http404("文档url异常！")
        else:
            ex_name = ex_name.lower()

        if ex_name == "pdf":
            res["Content-type"] = "application/pdf"
        elif ex_name == "zip":
            res["Content-type"] = "application/zip"
        elif ex_name == "doc":
            res["Content-type"] = "application/msword"
        elif ex_name == "xls":
            res["Content-type"] = "application/vnd.ms-excel"
        elif ex_name == "docx":
            res["Content-type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ex_name == "ppt":
            res["Content-type"] = "application/vnd.ms-powerpoint"
        elif ex_name == "pptx":
            res["Content-type"] = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        else:
            raise Http404("文档格式不正确！")

        doc_filename = escape_uri_path('某表格.xls')

        res["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(doc_filename)
        return res
