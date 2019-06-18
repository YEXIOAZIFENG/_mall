from django.views import View
from django import http
from django.core.cache import cache

from .models import Area
from meiduo_mall.utils.response_code import RETCODE


class AreasView(View):
    """省市区数据查询"""

    def get(self, request):

        # 获取查询参数area_id
        area_id = request.GET.get('area_id')

        # 如果前端没有传area_id代表要查询所有省
        if area_id is None:
            # 先尝试着去缓存中找所有省数据
            province_list = cache.get('province_list')
            # 如果缓存中没有所有省数据,就去mysql查询
            if province_list is None:
                # 查询所有省:
                # 查询所有省的模型,得到所有省的查询集
                province_qs = Area.objects.filter(parent=None)
                # 遍历查询集,将里面的每一个模型对象转换成字典对象,再包装到列表中
                province_list = []  # 用来装每一个省的字典对象
                for province_model in province_qs:
                    province_list.append(
                        {
                            'id': province_model.id,
                            'name': province_model.name
                        }
                    )
                # 从mysql查询出来之后立即设置缓存 缓存一个小时
                cache.set('province_list', province_list, 3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 先尝试取缓存
            sub_data = cache.get('sub_area_%s' % area_id)
            if sub_data is None:
                # 如果前端传了area_id,代表查询指定省下面的所有市,或指定市下面的所有区
                subs_qs = Area.objects.filter(parent_id=area_id)
                try:
                    # 查询当前指定的上级行政区
                    parent_model = Area.objects.get(id=area_id)
                except Area.DoesNotExist:
                    return http.HttpResponseForbidden('area_id不存在')

                sub_list = []  # 用来装所有下级行政区字典数据
                for sub_model in subs_qs:
                    sub_list.append({
                        'id': sub_model.id,
                        'name': sub_model.name
                    })

                # 构造完整数据
                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': sub_list  # 下级所有行政区数据
                }
                # 设置缓存
                cache.set('sub_area_%s' % area_id, sub_data, 3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
