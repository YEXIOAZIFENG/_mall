
from rest_framework.views import APIView
from meiduo_admin.serializers.login_serializer import *
from rest_framework.response import Response

class LoginView(APIView):

    # POST
    # meiduo_admin/authorizations/
    def post(self, request):
        # 使用序列化器实现用户传统登陆，token签发

        # 1、构建序列化器对象
        s = LoginSerializer(data=request.data)
        # 2、数据校验
        s.is_valid(raise_exception=True)
        # 3、序列化返回
        # return Response(s.data)
        return Response({
            "username": s.validated_data['user'].username,
            "user_id": s.validated_data['user'].id,
            "token": s.validated_data['token'],
        })