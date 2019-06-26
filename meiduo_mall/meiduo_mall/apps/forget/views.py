from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from django.views import View

from contents.models import ContentCategory
from contents.utils import get_categories


class ForgetView(View):
    """假装首页"""

    def get(self, request):
        # 定义一个大字典用来装所有广告
        contents = {}
        # 获取出所有广告类别数据
        content_category_qs = ContentCategory.objects.all()
        for content_category in content_category_qs:
            # 包装每种类型的广告数据
            contents[content_category.key] = content_category.content_set.filter(status=True).order_by('sequence')

        # 包装要渲染的数据
        context = {
            'categories': get_categories(),  # 商品分类数据
            'contents': contents,  # 广告内容
        }
        return render(request, 'forget.html', context)

