from django.conf.urls import url
from . import views

urlpatterns = [

    url(r'^weibo/authorization/$', views.OauthWeiBologinView.as_view()),
    url(r'^sina_callback/$', views.OauthWeiBoView.as_view()),
    url(r'^oauth/sina/user/$', views.OauthWeiBoView.as_view()),

]
