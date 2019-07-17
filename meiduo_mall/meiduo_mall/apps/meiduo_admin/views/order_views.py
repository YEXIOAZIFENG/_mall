from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from orders.models import OrderInfo
from meiduo_admin.serializers.order_serializers import *
from meiduo_admin.pages import MyPage


class OrderInfoView(ListAPIView):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderInfoSimplerSerializer
    pagination_class = MyPage

    # orders/?keyword=xxx
    def get_queryset(self):
        # 根据订单id过滤
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()


class OrderInfoDetailView(RetrieveAPIView, UpdateAPIView):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderInfoDetailSerializer
