from django.conf.urls import urlfrom . import viewsurlpatterns = [    # 展示订单结算页面    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),    # 提交订单    url(r'^orders/commit/$', views.OrderCommitView.as_view()),    # 展示提交订单成功后的页面    url(r'^orders/success/$', views.OrderSuccessView.as_view()),]