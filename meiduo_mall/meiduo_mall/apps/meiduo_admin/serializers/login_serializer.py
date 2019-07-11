
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_jwt.utils import jwt_payload_handler,jwt_encode_handler

# 定义序列化器
# 业务流程：对用户名和密码校验，签发token值

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    token = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        # 1、attr：用户名和密码
        # username = attrs.get("username")
        # password = attrs.get("password")

        # 2、用户身份验证（传统验证）
        # authenticate(username=username, password=password)
        user = authenticate(**attrs) # 返回认证成功的用户对象，如果返回None说明认证失败

        if not user:
            # 认证失败了
            raise serializers.ValidationError("用户名或密码错误!")

        # 3、验证通过，签发token
        payload = jwt_payload_handler(user)
        jwt_token = jwt_encode_handler(payload)

        # 有效数据返回
        # return {
        #     "username": user.username,
        #     "user_id": user.id,
        #     "token": jwt_token
        # }
        return {
            "user": user,
            "token": jwt_token
        }
