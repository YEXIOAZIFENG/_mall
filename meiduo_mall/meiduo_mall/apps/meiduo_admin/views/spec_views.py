from rest_framework.viewsets import ModelViewSet
# from goods.models import SPUSpecification
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.spec_serializers import *


class SpecViewSet(ModelViewSet):
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecSimpleSerializer
    pagination_class = MyPage
