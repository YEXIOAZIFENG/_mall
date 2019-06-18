from django.shortcuts import render, redirect
from django.views import View
from django import http
import re, json
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins

from .models import User
from meiduo_mall.utils.response_code import RETCODE
from .utils import generate_verify_email_url, check_verify_email_token
from celery_tasks.email.tasks import send_verify_email


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
        if all([username, password, password2, mobile, sms_code, allow]) is False:
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
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 获取reids中短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        # 判断验证码是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码已过期')
        # 删除reids中已被使用过的短信验证
        redis_conn.delete('sms_%s' % mobile)
        # 由bytes转换为str
        sms_code_server = sms_code_server.decode()
        # 判断用户输入的短信验证码是否正确
        if sms_code != sms_code_server:
            return http.HttpResponseForbidden('请输入正确的短信验证码')

        # 业务逻辑处理
        # user = User.objects.create(password=password)
        # user.set_password(password)
        # user.save()
        # create_user 方法会对password进行加密
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 用户注册成功后即代表登录,需要做状态保持本质是将当前用户的id存储到session
        login(request, user)

        # # 响应  http://127.0.0.1:8000/
        # return redirect('/')

        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        # 登录成功重定向到首页
        return response


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


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """展示登录界面"""
        return render(request, 'login.html')

    # def post(self, request):
    #     """实现用户登录"""
    #     # 接收请求体中的表单数据
    #     query_dict = request.POST
    #     username = query_dict.get('username')
    #     password = query_dict.get('password')
    #     remembered = query_dict.get('remembered')
    #
    #     # 判断当前用户是不是在用手机号登录,如果是手机号登录让它在认证时就用mobile去查询user
    #     if re.match(r'^1[3-9]\d{9}$', username):
    #         User.USERNAME_FIELD = 'mobile'
    #
    #     # 登录认证
    #     user = authenticate(request, username=username, password=password)
    #     # user = User.objects.get(mobile=username)
    #     # ** {self.model.USERNAME_FIELD: username}
    #     # (mobile=username)
    #     # user.check_password(password)
    #     # return user
    #     if user is None:  # 如果if成立说明用户登录失败
    #         return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
    #     User.USERNAME_FIELD = 'username'
    #     # 状态保持
    #     login(request, user)
    #     # 判断用户是否勾选了记住登录
    #     if remembered is None:
    #         request.session.set_expiry(0)  # session过期时间指定为None默认是两周,指定为0是关闭浏览器删除
    #         # cookie如果指定过期时间为None 关闭浏览器删除, 如果指定0,它还没出生就byby了
    #
    #
    #     # 登录成功重定向到首页
    #     return redirect('/')

    def post(self, request):
        """实现用户登录"""
        # 接收请求体中的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # 登录认证
        user = authenticate(request, username=username, password=password)

        if user is None:  # 如果if成立说明用户登录失败
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 状态保持
        login(request, user)
        # 判断用户是否勾选了记住登录
        if remembered is None:
            request.session.set_expiry(0)
            # session过期时间指定为None默认是两周,指定为0是关闭浏览器删除
            # cookie如果指定过期时间为None 关闭浏览器删除, 如果指定0,它还没出生就没了

        # 当用户登录成功后向cookie中存储当前登录用户的username

        # response = redirect(request.GET.get('next') or '/')
        response = redirect(request.GET.get('next', '/'))
        response.set_cookie('username', user.username, max_age=(settings.SESSION_COOKIE_AGE if remembered else None))

        # 登录成功重定向到首页
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        # 清除状态保持数据
        logout(request)
        # 重定向到login
        # http:127.0.0.1:8000/login/
        response = redirect('/login/')
        # 清除cookie中的username
        response.delete_cookie('username')

        return response


class InfoView(mixins.LoginRequiredMixin, View):
    """展示用户中心"""

    @staticmethod
    def get(request):
        # 判断用户是否登录, 如果登录显示个人中心界面
        return render(request, 'user_center_info.html')


class EmailView(mixins.LoginRequiredMixin, View):
    """添加邮箱"""

    def put(self, request):
        json_str = request.body.decode()  # body返回的是bytes
        json_dict = json.loads(json_str)  # 将json字符串转换成json字典
        email = json_dict.get('email')

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱格式错误')

        # 获取登录用户user模型对象
        user = request.user
        # 给user的email字段赋值
        user.email = email
        user.save()

        # 设置完邮箱那一刻就对用户邮箱发个邮件
        # send_mail()
        # 生成邮箱激活url
        verify_url = generate_verify_email_url(user)
        # celery进行异步发送邮件
        send_verify_email.delay(email, verify_url)

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class EmailVerificationView(View):
    """激活邮箱"""

    def get(self, request):

        # 获取url中查询参数
        token = request.GET.get('token')

        if token is None:
            return http.HttpResponseForbidden('缺少token参数')

        # 对token进行解密并查询到要激活邮箱的那个用户
        user = check_verify_email_token(token)
        # 如果没有查询到user,提前响应
        if user is None:
            return http.HttpResponseForbidden('token无效')
        # 如果查询到user,修改它的email_active字段为True,再save()
        user.email_active = True
        user.save()
        # 响应
        # return render(request, 'user_center_info.html')
        return redirect('/info/')


class AddressView(mixins.LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""
        return render(request, 'user_center_site.html')
