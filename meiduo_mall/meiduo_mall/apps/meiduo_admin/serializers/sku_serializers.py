from rest_framework import serializers
from goods.models import SKU, SKUSpecification, GoodsCategory, SPU, SPUSpecification, SpecificationOption


class SKUSpecSerializer(serializers.ModelSerializer):
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification
        fields = ['spec_id', 'option_id']


class SKUSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    # specs 指的是什么? 与当前sku对象关联所有从表（SKUSpecification）数据集
    specs = SKUSpecSerializer(many=True, read_only=True)

    class Meta:
        model = SKU
        fields = "__all__"


class GoodsCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name']


class SPUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id', 'name']


class SpecOptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ['id', 'value']


class SPUSpecSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    # 代表的是与当前spu对象关联的从表（SpecificationOption）的所有数据集
    # spu: 颜色；  options: [红色， 蓝色]
    options = SpecOptSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = [
            'id',
            'name',
            'spu',
            'spu_id',
            'options'
        ]
