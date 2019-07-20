from rest_framework import serializers
from users.models import User
from django.contrib.auth.hashers import make_password


class AdminPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'mobile',

            'groups',
            'user_permissions',

            'password',
        ]

        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        # groups = validated_data.pop('groups') # [1,2,3...]
        # user_permissions = validated_data.pop('user_permissions') # [9,7,6]
        #
        # # instance是主表对象
        # instance = User.objects.create_superuser(**validated_data)
        #
        # # instance.id --> 12
        # # user_group:   12   1
        # #               12   2
        # #               12   3
        # instance.groups.set(groups)
        # instance.user_permissions.set(user_permissions)
        # instance.save()
        #
        # return instance

        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_staff'] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)
