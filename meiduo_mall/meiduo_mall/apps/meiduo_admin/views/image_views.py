from rest_framework.viewsets import ModelViewSet
from goods.models import SKUImage, SKU
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.image_serializers import *
from meiduo_admin.pages import MyPage


class ImageViewSet(ModelViewSet):
    queryset = SKUImage.objects.all()
    serializer_class = SKUImageSerializer
    pagination_class = MyPage


class SKUView(ListAPIView):
    queryset = SKU.objects.all()
    serializer_class = SKUSimpleSerializer
