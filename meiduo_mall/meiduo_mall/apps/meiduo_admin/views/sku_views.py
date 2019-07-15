from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from goods.models import SKU, GoodsCategory, SPU, SPUSpecification
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.sku_serializers import SKUSerializer, GoodsCategorySimpleSerializer, SPUSpecSerializer, \
    SPUSimpleSerializer


class SKUViewSet(ModelViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUSerializer
    pagination_class = MyPage

    def get_queryset(self):
        if self.action == "categories":
            return GoodsCategory.objects.filter(parent_id__gt=37)

        if self.action == "simple":
            return SPU.objects.all()

        if self.action == "specs":
            return SPUSpecification.objects.filter(spu_id=self.kwargs['pk'])

        keyword = self.request.query_params.get("keyword")
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()

    def get_serializer_class(self):
        if self.action == "categories":
            return GoodsCategorySimpleSerializer
        if self.action == "simple":
            return SPUSimpleSerializer
        if self.action == "specs":
            return SPUSpecSerializer

        return self.serializer_class

    @action(methods=['get'], detail=False)
    def categories(self, request):
        """
        将三级分类信息返回
        :param request:
        :return:
        """
        cates = self.get_queryset()
        # 三级分类的数据集
        # cates = GoodsCategory.objects.filter(parent_id__gt=37)
        # 获得序列化器
        # cates_serializer = GoodsCategorySimpleSerializer(cates, many=True)
        cates_serializer = self.get_serializer(cates, many=True)
        return Response(cates_serializer.data)

    # GET
    # goods/simple/
    @action(methods=['get'], detail=False)
    def simple(self, request):
        spu_query = self.get_queryset()
        spu_serializer = self.get_serializer(spu_query, many=True)
        return Response(spu_serializer.data)

    # GET
    # goods/(?P<pk>\d+)/specs/
    @action(methods=['get'], detail=True)
    def specs(self, request, pk):
        specs_queryset = self.get_queryset()
        serializer = self.get_serializer(specs_queryset, many=True)
        return Response(serializer.data)
