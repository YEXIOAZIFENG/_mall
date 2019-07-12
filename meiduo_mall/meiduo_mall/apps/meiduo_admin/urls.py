from django.conf.urls import url, include
from django.contrib import admin
from meiduo_admin.views.login_views import LoginView

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import SimpleRouter

from meiduo_admin.views.home_views import HomeViewSet

urlpatterns = [
    # url(r'^authorizations/$', LoginView.as_view()),

    url(r'^authorizations/$', obtain_jwt_token),
]

router = SimpleRouter()
# statistical/total_count/
router.register(prefix="statistical", viewset=HomeViewSet, base_name="home")
urlpatterns += router.urls
