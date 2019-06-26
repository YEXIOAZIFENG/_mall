from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^forget/', views.ForgetView.as_view()),

]
