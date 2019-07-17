from rest_framework import serializers
from orders.models import OrderInfo, OrderGoods
from goods.models import SKU


class OrderInfoSimplerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = [
            'order_id',
            'create_time'
        ]


class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = [
            'name',
            'default_image',
        ]


class OrderGoodsSerializer(serializers.ModelSerializer):
    # 关联的是与当前OrderGoods（从表对象）的主表对象（单一）
    sku = SKUSimpleSerializer()

    class Meta:
        model = OrderGoods
        fields = [
            'count',
            'price',
            'sku'
        ]


class OrderInfoDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    # 从表数据集
    skus = OrderGoodsSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = "__all__"
