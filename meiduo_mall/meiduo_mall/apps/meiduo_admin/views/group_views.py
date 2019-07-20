from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
# from django.contrib.auth.models import Group, Permission
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.group_serializers import *
from meiduo_admin.serializers.perm_serializers import *


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSimplerSerializer
    pagination_class = MyPage


class GroupPermView(ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermSerializer
