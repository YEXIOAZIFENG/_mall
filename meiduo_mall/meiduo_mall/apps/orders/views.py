from django.shortcuts import render
from django_redis import get_redis_connection
from decimal import Decimal
from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from goods.models import SKU


class OrderSettlementView(LoginRequiredView):
    """去结算"""

    def get(self, request):

        user = request.user
        # 查询当前用户的所有收货地址
        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 判断用户是否有收货地址
        if addresses.exists() is False:
            addresses = None

        # 创建redis连接对象
        redis_conn = get_redis_connection('carts')
        # 获取redis中购物车的hash数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        # 获取redis中购物车勾选状态set集合数据
        selected_ids = redis_conn.smembers('selected_%s' % user.id)

        # 对hash字典购物车数据进行过滤,只勾选商品数据
        cart_dict = {}  # 用来包装所有勾选商品的sku_id,及count  {sku_id_16: count, sku_id_1: count}
        for sku_id_bytes in selected_ids:  # 遍历set集合,拿到勾选商品的sku_id
            cart_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])

        # 根据sku_id查询到指定的sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 定义要购买商品总数量和总价变量
        total_count = 0
        total_amount = 0
        # 邮费
        freight = Decimal('10.00')

        # 遍历skus查询集,给每个sku模型多定义两个属性,count, amount
        for sku in skus:
            sku.count = cart_dict[sku.id]
            sku.amount = sku.price * sku.count
            total_count += sku.count
            total_amount += sku.amount

        # 包装模型渲染时需要用到的数据
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }
        #
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredView):
    """提交订单"""

    def post(self, request):

        pass
