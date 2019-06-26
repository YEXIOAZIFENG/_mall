import base64
import pickle

from django import http
from django.shortcuts import render
from django.views import View
import json

from django_redis import get_redis_connection

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE


class CartsView(View):

    def post(self, request):
        """添加购物车"""
        # 接收和校验参数
        # 判断用户是否登录
        """添加购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 校验
        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数有误')

        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数有误')

        user = request.user
        if user.is_authenticated:

            # 用户已登录，操作redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 新增购物车数据
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 新增选中的状态
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            # 执行管道
            pl.execute()
            # 响应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

        else:
            # 未登录用户存储购物车数据到cookie
            # 获取cookie中购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断cookie中是否有购物车数据
            if cart_str:
                # 如果取到了cookie购物车数据,将字符串转回字典
                cart_str_bytes = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_bytes)

                # cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                # 判断当前要添加到商品是否已经添加过,如果添加过,对count做增量
                if sku_id in cart_dict:
                    # 取出已经添加过的商品原有要购物车数量
                    origin_count = cart_dict[sku_id]['count']
                    count += origin_count

            else:
                # 如果没有cookie购物车数据, 准备一个大字典
                cart_dict = {}

            # 如果本次添加的是一个新商品,就增加到大字典
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将购物车大字典,再转回到字符串
            # cart_bytes = pickle.dumps(cart_dict)
            # cart_str_bytes = base64.b64encode(cart_bytes)
            # cart_str = cart_str_bytes.decode()
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

            # 设置cookie
            response.set_cookie('carts', cart_str)

            return response

    def get(self, request):
        """购物车数据展示"""

        # 获取当前user
        user = request.user
        # 判断当前用户是否登录
        if user.is_authenticated:
            # 如果登录从redis中获取出购物车数据
            redis_conn = get_redis_connection('carts')
            # 获取hash数据  {'sku_id_1: count}
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取set集合中商品勾选状态 {sku_id_1}
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            """
                {
                    sku_id_1: {'count': 1, 'selected': True},
                    sku_id_2: {'count': 2, 'selected': False},

                }
            """
            # 把redis购物车数据 hash和 set集合向cookie购物车数据格式转换,目的为了,后期代码只写一遍
            cart_dict = {}  # 用来包装redis购物车数据字典
            for sku_id_bytes in redis_carts:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }
        else:
            # 如果未登录,从cookie中获取购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断当前有没有cookie购物车数据
            if cart_str:
                # 需要将购物车字符串数据转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie购物车数据
                return render(request, 'cart.html')

        # 根据sku_id查询到sku
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        cart_skus = []  # 包装前端需要渲染的购物车商品所有数据
        for sku in sku_qs:
            cart_skus.append(
                {
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'price': str(sku.price),  # 为了方便前端解析此数据
                    'count': cart_dict[sku.id]['count'],
                    'selected': str(cart_dict[sku.id]['selected']),  # js中的bool  true,false
                    'amount': str(sku.price * cart_dict[sku.id]['count'])
                }
            )
        # 包装模板需要进行渲染的数据
        return render(request, 'cart.html', {'cart_skus': cart_skus})

    def put(self, request):
        """修改购物车逻辑"""
        # 接收请求体数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')
        # 校验
        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden("缺少必传参数")

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        try:
            count = int(count)
            # if count < 0:
        except Exception:
            return http.HttpResponseForbidden('参数类型有误')

        if count < 0 or isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数类型有误')

        # 判断用户是否登录
        user = request.user
        # 包装商品修改后的前端数据
        cart_sku = {
            'id': sku.id,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': str(sku.price),  # 为了方便前端解析此数据
            'count': count,
            'selected': selected,  # js中的bool  true,false
            'amount': str(sku.price * count)
        }
        # 创建响应对象
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车数据成功', 'cart_sku': cart_sku})
        if user.is_authenticated:
            # 登录操作redis购物车数据
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 直接修改hash中的数据  覆盖count
            pl.hset('carts_%s' % user.id, sku_id, count)
            # 勾选状态
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            pl.execute()
            # return response
        else:
            # 未登录操作cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 判断是否有cookie
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return render(request, 'cart.html')

            # 直接新数据覆盖cookie大字典旧数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 将字典转换成字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 创建响应对象
            # 包装商品修改后的前端数据
            # cart_sku = {
            #     'id': sku.id,
            #     'name': sku.name,
            #     'default_image_url': sku.default_image.url,
            #     'price': str(sku.price),  # 为了方便前端解析此数据
            #     'count': cart_dict[sku.id]['count'],
            #     'selected': str(cart_dict[sku.id]['selected']),  # js中的bool  true,false
            #     'amount': str(sku.price * cart_dict[sku.id]['count'])
            # }
            # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车数据成功', 'cart_sku'})
            response.set_cookie('carts', cart_str)

        return response

    def delete(self, request):
        """删除购物车数据"""

        # 接收sku_id
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        # 获取当前user
        user = request.user

        # 判断是否登录
        if user.is_authenticated:
            # 登录用户操作redis购物车数据
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除商品hash数据
            pl.hdel('carts_%s' % user.id, sku_id)
            # 删除商品set集合数据
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return http.JsonResponse({"code": RETCODE.OK, 'errmsg': '删除购物车成功'})
        else:
            # 未登录用户操作cookie购物车数据
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断是否获取到cookie数据
            if cart_str:
                # 如果有cookie购物车数据将字符串转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie购物车数据,提前响应
                return http.HttpResponseForbidden('缺少cookie')
            # 把当前sku_id对就的键值对从cart_dict删除
            if sku_id in cart_dict:
                del cart_dict[sku_id]  # 判断当前要删除的商品存在时,再去删除

            # 创建响应对象
            response = http.JsonResponse({"code": RETCODE.OK, 'errmsg': '删除购物车成功'})
            # 如果当前cookie购物车数据已经全部删除了
            if not cart_dict:
                # 直接把cookie中的购物车数据删除
                response.delete_cookie('carts')
                return response

            # 把字典再转回字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 设置cookie
            response.set_cookie('carts', cart_str)
            # 响应
            return response


class CartsSelectedAllView(View):
    """购物车全选"""

    def put(self, request):

        # 接收selected
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')

        # 校验
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数类型有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 登录用户操作redis
            # 创建redis连接
            redis_conn = get_redis_connection('carts')
            # 获取hash字典数据
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 如果是全选,把hash中的所有sku_id添加到set集合中
            if selected:
                redis_conn.sadd('selected_%s' % user.id, *redis_carts.keys())
            # 如果是取消全选,直接移除redis的set集合
            else:
                redis_conn.delete('selected_%s' % user.id)
                # redis_conn.srem('selected_%s' % user.id, *redis_carts.keys())
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:

            # 未登录操作cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return http.HttpResponseForbidden('cookie没有获取到')

            # 遍历cookie字典将里面的selected全部改为前端传入的状态
            for sku_dict in cart_dict.values():
                sku_dict['selected'] = selected

            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            response.set_cookie('carts', cart_str)
            return response


class CartsSimpleView(View):
    """mini版购物车展示"""

    def get(self, request):
        # 获取当前user
        user = request.user
        # 判断当前用户是否登录
        if user.is_authenticated:
            # 如果登录从redis中获取出购物车数据
            redis_conn = get_redis_connection('carts')
            # 获取hash数据  {'sku_id_1: count}
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取set集合中商品勾选状态 {sku_id_1}
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            """
                {
                    sku_id_1: {'count': 1, 'selected': True},
                    sku_id_2: {'count': 2, 'selected': False},

                }
            """
            # 把redis购物车数据 hash和 set集合向cookie购物车数据格式转换,目的为了,后期代码只写一遍
            cart_dict = {}  # 用来包装redis购物车数据字典
            for sku_id_bytes in redis_carts:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }
        else:
            # 如果未登录,从cookie中获取购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断当前有没有cookie购物车数据
            if cart_str:
                # 需要将购物车字符串数据转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie购物车数据
                return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有数据', 'cart_skus': []})

        # 根据sku_id查询到sku
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        cart_skus = []  # 包装前端需要渲染的购物车商品所有数据
        for sku in sku_qs:
            cart_skus.append(
                {
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'count': cart_dict[sku.id]['count'],
                }
            )
        # 如果没有cookie购物车数据
        return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有数据', 'cart_skus': cart_skus})
