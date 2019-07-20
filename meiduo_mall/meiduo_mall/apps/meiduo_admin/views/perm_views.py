from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
# from django.contrib.auth.models import Permission
from meiduo_admin.serializers.perm_serializers import *
from meiduo_admin.pages import MyPage


class PermViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermSerializer
    pagination_class = MyPage


class ContentTypeView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
