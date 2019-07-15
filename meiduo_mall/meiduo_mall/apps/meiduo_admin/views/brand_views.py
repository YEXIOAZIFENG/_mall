from rest_framework.viewsets import ModelViewSet
from goods.models import Brand
from meiduo_admin.serializers.brand_serializers import *
from meiduo_admin.pages import MyPage


class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = MyPage
