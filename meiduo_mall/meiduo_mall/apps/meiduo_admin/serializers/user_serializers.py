from rest_framework import serializers
from users.models import User
from django.contrib.auth.hashers import make_password


# 定义一个序列化器，将User模型类
# 序列化成id，username，mobile和email

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'mobile',
            'email',

            'password'
        ]

        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    def create(self, validated_data):
        # validated_data['password'] = make_password(validated_data['password'])
        # validated_data['is_staff'] = True
        # return super().create(validated_data)

        return self.Meta.model.objects.create_superuser(**validated_data)

    # def validate(self, attrs):
    #     """
    #     数据校验，最终返回有效数据，这个有效数据就是用来构建新的模型类对象
    #     self.create 中就使用了该有效数据创建
    #     问题： 有效数据中密码是明文的，有效数据中没有is_staff=True
    #     :param attrs:
    #     :return:
    #     """
    #     # 加密，获得密文密码
    #     password = attrs.get("password")
    #     password = make_password(password)
    #     # 更新有效数据
    #     attrs['password'] = password
    #     attrs['is_staff'] = True
    #
    #     return attrs
