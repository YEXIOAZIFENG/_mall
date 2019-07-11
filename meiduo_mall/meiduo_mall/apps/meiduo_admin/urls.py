
from django.conf.urls import url, include
from django.contrib import admin
from meiduo_admin.views.login_views import LoginView
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
   # url(r'^authorizations/$', LoginView.as_view()),

   url(r'^authorizations/$', obtain_jwt_token),
]
