import re

from django import http
from django.shortcuts import redirect, render
from django.views import View
from django.conf import settings
from django.contrib.auth import login
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.sina import OAuth_WEIBO
from users.models import User
from .models import OAuthWeiBoUser
from carts.utils import merge_cart_cookie_to_redis
from meiduo_mall.apps.oauth.utils import generate_openid_signature, check_openid_signature


class OauthWeiBologinView(View):
    """ 构建微博登录跳转链接 """

    def get(self, request):
        next = request.GET.get('next')
        # 1、创建微博对象
        sina = OAuth_WEIBO(
            client_id=settings.WEIBO_CLIENT_ID,
            client_key=settings.WEIBO__CLIENT_SECRET,
            redirect_url=settings.WEIBO__REDIRECT_URI,
            state=next

        )

        # 4、构建跳转连接
        login_url = sina.get_auth_url()

        # 5、返回跳转连接
        # return Response({'login_url': login_url})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'Ok', 'login_url': login_url})


class OauthWeiBoView(View):
    """回调处理"""

    def get(self, request):

        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden("缺少code")

        # 创建工具对象
        sina = OAuth_WEIBO(
            client_id=settings.WEIBO_CLIENT_ID,
            client_key=settings.WEIBO__CLIENT_SECRET,
            redirect_url=settings.WEIBO__REDIRECT_URI)

        try:
            # 使用code查询向服务器请求token  # 拿到openid(uid)
            openid = sina.get_access_token(code)
        except Exception as e:
            # 未拿到openid(uid)
            return http.HttpResponseServerError('OAuth2.0认证失败')

        try:
            # 尝试使用openid 向数据库中匹配
            sina_user = OAuthWeiBoUser.objects.get(openid=openid)
        except OAuthWeiBoUser.DoesNotExist:
            # 如果未查询到数据代表第一次登录，新建用户数据与openid进行绑定
            # 渲染新用户界面，而在此之前需要将openid加密存于页面当中，以便后续拿来与用户绑定
            openid = generate_openid_signature(openid)

            return render(request, 'sina_callback.html', {'openid': openid})

        else:
            # 如果查询到数据代表此weibo之前已有绑定，直接登录
            sina_user = sina_user.user
            # 实现状态保持，重定向到来源页面，设置cookie，返回响应对象
            login(request, sina_user)
            next = request.GET.get('state', '/')
            response = redirect(next)
            response.set_cookie('username', sina_user.username, max_age=settings.SESSION_COOKIE_AGE)
            merge_cart_cookie_to_redis(request, response)
            return response

    def post(self, request):

        mobile = request.POST.get('mobile')
        pwd = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        openid = request.POST.get('openid')
        # 校验数据
        if not all([mobile, pwd, sms_code_client, openid]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', pwd):
            return http.HttpResponseForbidden('请输入8—20位密码')
        # 校验手机验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return http.HttpResponseForbidden('手机验证码过期')
        redis_conn.delete('sms_%s' % mobile)
        sms_code_server = sms_code_server.decode()
        if sms_code_server != sms_code_client:
            return http.HttpResponseForbidden('请输入正确的手机验证码')
        # 对openid进行解密
        openid = check_openid_signature(openid)
        try:
            # 用手机号查询数据库用户是否存在，如存在，校验密码后绑定openid
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果不存在，则创建新的User用户，然后再进行openid的绑定
            user = User.objects.create_user(username=mobile, password=pwd, mobile=mobile)
        else:
            if not user.check_password(pwd):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或者密码错误'})

        # 此时user用户已验证通过或者新建成功，可进行与openid的绑定处理
        OAuthWeiBoUser.objects.create(openid=openid, user=user)
        # 进行状态保持，重定向、设置cookie、返回响应对象
        login(request, user)
        next = request.GET.get("state", '/')
        response = redirect(next)
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        # 登录成功合并购物车
        merge_cart_cookie_to_redis(request, response)
        return response
