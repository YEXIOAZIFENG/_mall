from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from goods.models import SPU, Brand, GoodsCategory
from meiduo_admin.serializers.spu_serializers import *
from meiduo_admin.pages import MyPage


class SPUViewSet(ModelViewSet):
    queryset = SPU.objects.all()
    serializer_class = SPUSerializer
    pagination_class = MyPage


# 构建一个视图，处理Brand模型类，获得品牌所有数据
class BrandSimpleView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Brand.objects.all()
    serializer_class = BrandSimpleSerializer


# 视图，响应获取一级分类数据
class GoodsCategorySimpleView(ListAPIView):
    permission_classes = [IsAdminUser]
    # queryset = GoodsCategory.objects.filter(parent=None) # 一级分类对象的数据集
    queryset = GoodsCategory.objects.all()
    serializer_class = GoodsCategorySimpleSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk', None)
        if pk:
            # 说明给了我一个pk，要的数据是二级或三级信息
            return self.queryset.filter(parent_id=pk)
        # 如果路径无pk，说明前端需要的是一级分类
        return self.queryset.filter(parent=None)
