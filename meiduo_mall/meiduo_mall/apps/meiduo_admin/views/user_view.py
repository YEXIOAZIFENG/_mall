from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser

from users.models import User
from meiduo_admin.serializers.user_serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.generics import ListAPIView, CreateAPIView
from meiduo_admin.pages import MyPage


class UserView(ListAPIView, CreateAPIView):  # ListModelMixin, GenericAPIView):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserSerializer
    pagination_class = MyPage
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """
        根据字符串参数keyword过滤
        :return: 过滤后的数据集
        """

        keyword = self.request.query_params.get('keyword')
        # 如果请求字符串参数中有keyword，过滤（名字以keyword开头）
        if keyword:
            return (self.queryset.filter(username__icontains=keyword) or self.queryset.filter(
                mobile__icontains=keyword) or self.queryset.filter(
                email__icontains=keyword))
        # 如果没有keyword，返回默认处理的数据集
        return self.queryset.all()  # QuerySet： 1、惰性执行  2、缓存

# def get(self, request):
# return self.list(request)
# # 1、获得处理的所有用户的数据集
# user_queryset = self.get_queryset()
#
# # 1.1 对数据集分页
# # 返回值： page指的是分页的子集
# page = self.paginate_queryset(user_queryset)
#
# if page:
#     # 对这个子集进行序列化操作
#     page_serializer = self.get_serializer(page, many=True)
#
#     return self.get_paginated_response(page_serializer.data)
#
# # 2、获得序列化器对象
# us = self.get_serializer(user_queryset, many=True)
# # 3、序列化返回
# return Response(us.data)
