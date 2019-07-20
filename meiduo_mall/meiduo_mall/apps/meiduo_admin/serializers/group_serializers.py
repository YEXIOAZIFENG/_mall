from rest_framework import serializers
from django.contrib.auth.models import Group


class GroupSimplerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

        # extra_kwargs = {
        #     "permissions": {"write_only": True}
        # }
