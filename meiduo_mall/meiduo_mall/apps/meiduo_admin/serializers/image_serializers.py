from rest_framework import serializers
from goods.models import SKUImage, SKU
from fdfs_client.client import Fdfs_client
from django.conf import settings


class SKUImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKUImage
        fields = [
            'id',
            'sku',
            'image'
        ]

    def create(self, validated_data):
        # file是一个文件对象 -->  file = open("浏览器图片", "rb")
        # content = file.read()
        file = validated_data.pop("image")
        content = file.read()  # content: 上传来的文件"数据" byte:字节对象

        # 1.2 获得fdfs链接对象
        # conn = Fdfs_client('./meiduo_mall/client.conf')
        conn = Fdfs_client(settings.FDFS_CONFPATH)
        # 1.3 根据文件数据上传
        res = conn.upload_by_buffer(content)  # 传入数据也是字节对象
        if res['Status'] != 'Upload successed.':
            # 上传失败
            raise serializers.ValidationError("上传失败！")

        validated_data['image'] = res['Remote file_id']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        file = validated_data.pop("image")
        content = file.read()  # content: 上传来的文件"数据" byte:字节对象

        # 1.2 获得fdfs链接对象
        # conn = Fdfs_client('./meiduo_mall/client.conf')
        conn = Fdfs_client(settings.FDFS_CONFPATH)
        # 1.3 根据文件数据上传
        res = conn.upload_by_buffer(content)  # 传入数据也是字节对象
        if res['Status'] != 'Upload successed.':
            # 上传失败
            raise serializers.ValidationError("上传失败！")

        instance.image = res['Remote file_id']
        instance.save()

        return instance


class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'name']
