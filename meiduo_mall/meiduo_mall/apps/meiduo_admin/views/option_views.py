from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SpecificationOption, SPUSpecification
from meiduo_admin.serializers.option_serializers import *
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.spec_serializers import SpecSimpleSerializer


class SpecOptViewSet(ModelViewSet):
    queryset = SpecificationOption.objects.all()
    serializer_class = SpecOptSerializer
    pagination_class = MyPage


class SpecSimpleView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecSimpleSerializer
