from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.contrib.auth import login

from .models import User
from meiduo_mall.utils.response_code import RETCODE


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """注册业务逻辑"""

        # 接收请求体中的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')  # 后期再补充短信验证码的校验
        allow = query_dict.get('allow')  # 在表单中如果没有给单选框指定value值默认勾选 就是'on' 否则就是None

        # 校验数据  ''  ()  [] {}  None
        if all([username, password, password2, mobile, allow]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 短信验证码后期补充它的验证

        # 业务逻辑处理
        # user = User.objects.create(password=password)
        # user.set_password(password)
        # user.save()
        # create_user 方法会对password进行加密
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 用户注册成功后即代表登录,需要做状态保持本质是将当前用户的id存储到session
        login(request, user)

        # 响应  http://127.0.0.1:8000/
        return redirect('/')


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        # 使用username查询user表, 得到username的数量
        count = User.objects.filter(username=username).count()

        # 响应
        content = {'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'}  # 响应体数据
        return http.JsonResponse(content)


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        # 使用mobile查询user表, 得到mobile的数量
        count = User.objects.filter(mobile=mobile).count()

        # 响应
        content = {'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'}  # 响应体数据
        return http.JsonResponse(content)
