"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^', include('users.urls', namespace='users')),  # 用户模块

    url(r'^', include('contents.urls', namespace='contents')),  # 首页模块

    url(r'^', include('verifications.urls', namespace='verifications')),  # 验证码模块

    url(r'^', include('oauth.urls', namespace='oauth')),  # QQ模块

    url(r'^', include('areas.urls', namespace='areas')),  # 地址模块

    url(r'^', include('goods.urls', namespace='goods')),  # 列表模块

    url(r'^', include('carts.urls', namespace='carts')),  # 购物车模块

    url(r'^', include('orders.urls', namespace='order')),  # 订单模块

    url(r'^search/', include('haystack.urls')),  # 搜索模板

    url(r'^', include('payment.urls', namespace='payment')),  # 订单模块

    url(r'^', include('weibo_login.urls', namespace='weibo_login')),  # 微博登录

    url('^meiduo_admin/', include('meiduo_admin.urls', namespace='meiduo')),  # 美多后台
]
