from django.utils import timezone
from decimal import Decimal
from django.shortcuts import render
from django_redis import get_redis_connection
import json
from django import http
from django.db import transaction

from goods.models import SKU
from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from .models import OrderInfo, OrderGoods
from meiduo_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class OrderSettlementView(LoginRequiredView):
    """展示订单结算页面"""

    def get(self, request):
        user = request.user
        # 取出用户有效地址
        addresses = Address.objects.filter(user=user, is_deleted=False)
        if addresses.exists() is False:
            addresses = None

        # 取出用户购物车数据
        redis_conn = get_redis_connection("carts")
        redis_carts = redis_conn.hgetall("carts_%s" % user.id)  # 得到{{sku_id: 1}, {sku_id:2}}
        selected_ids = redis_conn.smembers("selected_%s" % user.id)
        # 构造用户选择结算的商品字典{商品1：3件，商品2：3件}
        carts_dict = {}
        for sku_id_bytes in selected_ids:
            carts_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])

        # 将前端需要的数据整理后返回
        total_count = 0
        total_amount = 0
        # 邮费
        freight = Decimal('10.00')
        ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=ids)
        for sku in skus:
            # 前端所需要的sku对象上需要有count,amount属性，故为其临时添加新属性
            sku.count = carts_dict[sku.id]
            sku.amount = sku.price * carts_dict[sku.id]
            total_count += sku.count
            total_amount += sku.amount
        # 包装响应数据：
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight

        }
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredView):
    """提交订单"""

    def post(self, request):
        # 前端传入address_id和pay_method,需要返回Json，内容是order_id,
        # 1、接收前端参数，校验参数，
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        user = request.user
        # 1.1 校验数据
        if all([address_id, pay_method]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('参数address_id有误')
        if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
            return http.HttpResponseForbidden('支付方式选择有误')
        # 2、新增订单记录，后取出购物车中商品信息
        # 2.1 生成一个订单编号  用时间拼接用户id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 2.2 根据支付方式获取支付状态status
        status = OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
            'ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']

        # 对于数据库的操作为保持一致性，手动开启事务
        with transaction.atomic():
            # 创建一个事务保存点,后期如操作不成功，可回滚到这里
            save_id = transaction.savepoint()
            try:
                order_model = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )
                # 2.3 取出购物车中hash\set数据
                redis_conn = get_redis_connection('carts')
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)
                # 2.4 准备一个新字典，筛选出要购买的商品{sku_id:count}
                cart_dict = {}
                for sku_id_bytes in selected_ids:
                    cart_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])
                # 取出sku_id,通过id取出sku模型集
                ids = cart_dict.keys()
                # 3、遍历购物车中的每一件商品，判断库存是否充足，
                for sku_id in ids:
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        buy_count = cart_dict[sku.id]
                        origin_count = sku.stock
                        origin_sales = sku.sales
                        if buy_count > origin_count:
                            # 库存不足则回滚操作
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 4、库存充足则此商品可成功下单，修改sku的库存（stock）与销量（sales）和spu的销量（sales）
                        new_count = origin_count - buy_count
                        new_sales = origin_sales + buy_count
                        # sku.stock = new_count
                        # sku.sales = new_sales
                        # sku.save()
                        # 使用乐观锁
                        result = SKU.objects.filter(id=sku_id, stock=origin_count).update(stock=new_count,
                                                                                          sales=new_sales)
                        # 如果修改结果为0,代表没修改成功，重新尝试下单
                        if result == 0:
                            continue
                        # 修改spu中的销量sales
                        sku.spu.sales += buy_count
                        sku.spu.save()

                        # 5、新增商品订单记录
                        OrderGoods.objects.create(
                            order_id=order_id,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )

                        # 6、修改订单中的商品总数和总价
                        order_model.total_count += buy_count
                        order_model.total_amount += (sku.price * buy_count)
                        break

                # 当商品都下单成功后，加上运费
                order_model.total_amount += order_model.freight
                order_model.save()
            except Exception as e:
                logger.error(e)
                # 如果数据库中操作有问题，直接暴力回滚到最初时候，并且响应下单失败
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})
            else:
                # 如果数据库修改过程中没有出现异常，则提交事务
                transaction.savepoint_commit(save_id)
        # 7、删除redis中已购买的商品信息
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *ids)
        pl.delete('selected_%s' % user.id)
        pl.execute()
        # 8、响应前端
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order_model.order_id})


class OrderSuccessView(LoginRequiredView):
    """展示成功订单页面"""

    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')
        try:
            OrderInfo.objects.get(order_id=order_id, total_amount=payment_amount, pay_method=pay_method)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)
