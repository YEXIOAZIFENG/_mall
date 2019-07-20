from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
# from users.models import User
from meiduo_admin.serializers.admin_serializers import *
from meiduo_admin.pages import MyPage
from django.contrib.auth.models import Group
from meiduo_admin.serializers.group_serializers import GroupSimplerSerializer


class AdminViewSet(ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminPermSerializer
    pagination_class = MyPage


class AdminGroupView(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSimplerSerializer
