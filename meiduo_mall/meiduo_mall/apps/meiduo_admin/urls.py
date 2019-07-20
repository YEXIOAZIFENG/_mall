from django.conf.urls import url, include
# from django.contrib import admin
# from meiduo_admin.views.login_views import LoginView
from rest_framework_jwt.views import obtain_jwt_token

from meiduo_admin.views.brand_views import BrandViewSet
from meiduo_admin.views.channels_views import ChannelViewSet, ChannelGroupView
from meiduo_admin.views.home_views import *
from rest_framework.routers import SimpleRouter

from meiduo_admin.views.image_views import ImageViewSet, SKUView
from meiduo_admin.views.order_views import OrderInfoView, OrderInfoDetailView
from meiduo_admin.views.perm_views import ContentTypeView
from meiduo_admin.views.user_view import *
from meiduo_admin.views.sku_views import *
from meiduo_admin.views.spu_views import *
from meiduo_admin.views.spec_views import *
from meiduo_admin.views.option_views import *

urlpatterns = [
    # url(r'^authorizations/$', LoginView.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^users/$', UserView.as_view()),
    # sku表
    url(r'^skus/$', SKUViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^skus/(?P<pk>\d+)/$', SKUViewSet.as_view({"get": "retrieve",
                                                    "put": "update",
                                                    "delete": "destroy"})),
    # 获得三级分类信息
    url(r'^skus/categories/$', SKUViewSet.as_view({"get": "categories"})),
    # 获得spu信息
    url(r'^goods/simple/$', SKUViewSet.as_view({"get": "simple"})),
    # 获得可选的spu规格及选项
    url(r'^goods/(?P<pk>\d+)/specs/$', SKUViewSet.as_view({"get": "specs"})),
    # SPU表
    url(r'^goods/$', SPUViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^goods/(?P<pk>\d+)/$', SPUViewSet.as_view({"get": "retrieve",
                                                     "put": "update",
                                                     "delete": "destroy"})),

    # 获得spu所属的品牌信息
    url(r'^goods/brands/simple/$', BrandSimpleView.as_view()),

    # 获得spu所属一级分类信息
    url(r'^goods/channel/categories/$', GoodsCategorySimpleView.as_view()),

    # 获得spu所属二级或三级分类信息
    url(r'^goods/channel/categories/(?P<pk>\d+)/$', GoodsCategorySimpleView.as_view()),

    # 规格表
    url(r'^goods/specs/$', SpecViewSet.as_view({"get": "list", "post": "create"})),

    url(r'^goods/specs/(?P<pk>\d+)/$', SpecViewSet.as_view({"get": "retrieve",
                                                            "put": "update",
                                                            "delete": "destroy"})),

    # 选项表
    url(r'specs/options/$', SpecOptViewSet.as_view({"get": "list", "post": "create"})),
    url(r'specs/options/(?P<pk>\d+)/$', SpecOptViewSet.as_view({"get": "retrieve",
                                                                "put": "update",
                                                                "delete": "destroy"})),
    # 获得新建选项数据的可选规格信息
    url(r'goods/specs/simple/$', SpecSimpleView.as_view()),

    # 频道表管理
    url(r'^goods/channels/$', ChannelViewSet.as_view({'get': 'list', "post": "create"})),
    url(r'^goods/channels/(?P<pk>\d+)/$', ChannelViewSet.as_view({'get': 'retrieve',
                                                                  'put': 'update',
                                                                  'delete': 'destroy'})),
    # 获得新增频道可选分组
    url(r'^goods/channel_types/$', ChannelGroupView.as_view()),
    # 获得新建频道可选一级分类
    url(r'^goods/categories/$', GoodsCategorySimpleView.as_view()),

    # 品牌表管理
    url(r'^goods/brands/$', BrandViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^goods/brands/(?P<pk>\d+)/$', BrandViewSet.as_view({"get": "retrieve",
                                                              'put': 'update',
                                                              'delete': 'destroy'})),

    # 图片表管理
    url(r'skus/images/$', ImageViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'skus/images/(?P<pk>\d+)/$', ImageViewSet.as_view({'get': 'retrieve',
                                                            'put': 'update',
                                                            'delete': 'destroy'})),

    # 获得新建图片可选sku数据
    url(r'skus/simple/$', SKUView.as_view()),

    # 获得多条订单数据
    url(r'orders/$', OrderInfoView.as_view()),
    # 获得订单详情数据
    url(r'orders/(?P<pk>\d+)/$', OrderInfoDetailView.as_view()),
    # 更新status
    url(r'orders/(?P<pk>\d+)/status/$', OrderInfoDetailView.as_view()),

    # 获得可选权限类型
    url(r'permission/content_types/$', ContentTypeView.as_view()),

]

router = SimpleRouter()
# statistical/total_count/
router.register(prefix="statistical", viewset=HomeViewSet, base_name="home")
# router.register(prefix="goods", viewset=SPUViewSet, base_name='spu')
urlpatterns += router.urls
