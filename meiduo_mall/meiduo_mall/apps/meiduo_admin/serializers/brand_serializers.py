from rest_framework import serializers
from goods.models import Brand
from fdfs_client.client import Fdfs_client
from django.conf import settings


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            'id',
            'name',
            'logo',
            'first_letter'
        ]

    def create(self, validated_data):
        # 1、文件fdfs上传
        # 1.1 获得上传的文件
        # file = open("chuangzhi1.jpg", "wb")
        # file.read() --> return bytes
        file = validated_data.pop("logo")
        content = file.read()  # content: 上传来的文件"数据" byte:字节对象

        # 1.2 获得fdfs链接对象
        # conn = Fdfs_client('./meiduo_mall/client.conf')
        conn = Fdfs_client(settings.FDFS_CONFPATH)
        # 1.3 根据文件数据上传
        res = conn.upload_by_buffer(content)  # 传入数据也是字节对象
        if res['Status'] != 'Upload successed.':
            # 上传失败
            raise serializers.ValidationError("上传失败！")

        # 2、获得文件上传后的file_id,在新建mysql数据(新建品牌对象)
        validated_data['logo'] = res['Remote file_id']

        return super().create(validated_data)

    def update(self, instance, validated_data):
        file = validated_data.pop("logo")
        content = file.read()  # content: 上传来的文件"数据" byte:字节对象

        # 1.2 获得fdfs链接对象
        # conn = Fdfs_client('./meiduo_mall/client.conf')
        conn = Fdfs_client(settings.FDFS_CONFPATH)

        # 1.3 根据文件数据上传
        res = conn.upload_by_buffer(content)  # 传入数据也是字节对象
        if res['Status'] != 'Upload successed.':
            # 上传失败
            raise serializers.ValidationError("上传失败！")

        # 更新当前brand对象的logo字段
        logo = res['Remote file_id']
        instance.logo = logo
        instance.save()

        return instance
