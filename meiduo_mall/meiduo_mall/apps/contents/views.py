from django.shortcuts import render
from django.views import View

from contents.models import ContentCategory
from contents.utils import get_categories


"""
categories = {
    '组号': {
                'channels': [] , # 当前组中的所有一级数据
                'sub_cats': [cat2.sub_cats, cat2],  # 当前组中的所有二级数据, 将来给每一个二级中多包装一个sub_cats用来保存它对应的三级
            }
    '组号' : {
                'channels': [],
                'sub_cats' : []
            }

}

广告数据:

contents = {
    '广告标识/广告类型': 某种类型下的所有广告,
    'index_lbt': [lbt1, lbt2,...],
    'index_kx': [kx1, kx2,...]

}

contents.index_lbt


"""
class IndexView(View):
    """首页广告"""

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
        return render(request, 'index.html', context)
