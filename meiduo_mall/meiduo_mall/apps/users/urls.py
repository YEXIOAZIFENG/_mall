from django.conf.urls import url

from . import views


urlpatterns = [
    # 用户注册
    url(r'^register/$', views.RegisterView.as_view()),
    # 判断用户名是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否重复
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 登陆界面
    url(r'^login/', views.LoginView.as_view()),
    # 登出界面
    url(r'^logout/', views.LogoutView.as_view()),
    # 用户中心
    url(r'^info/', views.InfoView.as_view()),
    # 设置邮箱
    url(r'^emails/$', views.EmailView.as_view()),
    # 邮箱激活
    url(r'^emails/verification/$', views.EmailVerificationView.as_view()),
    # 收貨地址
    url(r'^addresses/$', views.AddressView.as_view()),
    # 新增地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view()),
    # 修改和删除收货地址
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 修改收货地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateAddressTitleView.as_view()),
    # 设置默认收货地址
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 修改用户密码
    url(r'^password/$', views.ChangePasswordView.as_view()),
    # 商品历史浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistory.as_view()),
]