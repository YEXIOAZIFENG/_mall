import pytz
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import IsAdminUser

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from goods.models import GoodsVisitCount
from meiduo_admin.serializers.home_serializers import GoodsDaySerializer
from users.models import User


class HomeViewSet(ViewSet):
    # 请求方式： GET / meiduo_admin / statistical / total_count /
    permission_classes = [IsAdminUser]

    @action(methods=["get"], detail=False)
    def total_count(self, request):
        # 获取用户总数
        count = User.objects.count()

        date = timezone.now().date()

        return Response({
            "count": count,
            "date": date
        })

    # GET
    # statistical/day_increment/
    @action(methods=['get'], detail=False)
    def day_increment(self, request):
        # 构建返回数据
        # .now()--年月日十分秒
        # .date()--年月日
        # timezone.now() -->  当前时间（上海2019-7-11 9:45:56）
        # print(timezone.now()) -->  UTC时区： 2019-07-11 01:54:42.998445+00:00

        # 时间：年月日，十分秒，时区
        # 我如何才能够获取当前上海时间的零点 2019-7-11 0：0：0 Shanghai
        # 2019-07-11 10:03:25 +08:00
        # 2019-07-11 0:0:0 +08:06
        # d = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).replace(hour=0, minute=0,second=0)

        # 1、获取当日的零时
        date_0_shanghai = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) \
            .replace(hour=0, minute=0, second=0)

        # 2、根据零时，过滤用户
        count = User.objects.filter(date_joined__gte=date_0_shanghai).count()

        # 3、构建响应数据
        return Response({
            "count": count,
            "date": date_0_shanghai.date()
        })

    # GET
    # statistical/day_active/
    @action(methods=['get'], detail=False)
    def day_active(self, request):
        # 1、获取当日（Shanghai）零时
        date_0_shanghai = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) \
            .replace(hour=0, minute=0, second=0)

        # 2、过滤用户
        count = User.objects.filter(last_login__gte=date_0_shanghai).count()
        # 3、统计数据,构建返回
        return Response({
            "count": count,
            "date": date_0_shanghai.date()
        })

    # GET
    # statistical/day_orders/
    @action(methods=['get'], detail=False)
    def day_orders(self, request):
        # 统计日下单用户， User,OrderInfo

        # 已知条件： 当日的零时
        # 查询的目标数据：用户数量

        date_0_shanghai = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) \
            .replace(hour=0, minute=0, second=0)

        # 从从表查询
        # 1、过滤除当日下单的订单
        # order_queryset = OrderInfo.objects.filter(create_time__gte=date_0_shanghai)
        # 2、更具订单，统计出用户
        # user_list = []
        # for order in order_queryset:
        # order -- 订单对象
        # user_list.append(order.user)
        # 3、用户去重
        # count = len(set(user_list))

        # 从主表入手
        user_queryset = User.objects.filter(orderinfo__create_time__gte=date_0_shanghai)
        count = len(set(user_queryset))

        return Response({
            "count": count,
            "date": date_0_shanghai.date()
        })

    # GET
    # statistical/month_increment/
    @action(methods=['get'], detail=False)
    def month_increment(self, request):
        # 最近30天(包括当前),其中每一天的用户新建数量
        # 7-5 0:0:0   <= create_time  <   7-6 0:0:0

        cur_date = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))
        # start_date：其实日期为cur_date - (30 - 1)天
        start_date = cur_date - timedelta(days=29)  # 开始时间点

        date_list = []
        for index in range(30):
            # 每遍历一次，获得一个当日的时间（零时）
            # index: 0              1                   2
            # 开始时间： start_date   start_date + 1天    start_date + 2天
            clac_date = (start_date + timedelta(days=index)) \
                .replace(hour=0, minute=0, second=0)

            # 过滤用户
            count = User.objects.filter(date_joined__gte=clac_date,
                                        date_joined__lt=clac_date + timedelta(days=1)).count()

            date_list.append({
                "count": count,
                "date": clac_date.date()
            })

        return Response(date_list)

    # GET
    # statistical/goods_day_views/
    @action(methods=['get'], detail=False)
    def goods_day_views(self, request):
        # 1、获得序列化数据GoodsVisitCount
        date_0_shanghai = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) \
            .replace(hour=0, minute=0, second=0)
        gv = GoodsVisitCount.objects.filter(create_time__gte=date_0_shanghai)
        # 2、调用序列化器完成数据序列化
        gvs = GoodsDaySerializer(gv, many=True)
        # 3、构建响应对象
        return Response(gvs.data)
