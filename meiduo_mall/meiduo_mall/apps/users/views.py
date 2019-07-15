from django.conf import settings
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponseForbidden
import re, json, pickle, base64
from django.contrib.auth import login, authenticate, logout, mixins
from .models import User
from django import http
from django.utils.decorators import method_decorator
from django_redis import get_redis_connection
from django.core.paginator import Paginator, EmptyPage

from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView
from .utils import generate_verify_email_url, check_verify_email_token
from celery_tasks.email.tasks import send_verify_email
from .models import Address
from goods.models import SKU
from carts.utils import merge_cart_cookie_to_redis

from orders.models import OrderInfo, OrderGoods

from random import randint
from celery_tasks.sms.tasks import send_sms_code
import logging

logger = logging.getLogger('django')


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

    def get(self, request):
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
        user = request.user
        # 查询出来当前用户的所有未被逻辑删除的收货地址
        address_qs = Address.objects.filter(user=user, is_deleted=False)

        # 把查询集里面的模型转换成字典,然后再添加到列表中
        addresses_list = []
        for address_model in address_qs:
            addresses_list.append({
                'id': address_model.id,
                'title': address_model.title,
                'receiver': address_model.receiver,
                'province_id': address_model.province_id,
                'province': address_model.province.name,
                'city_id': address_model.city_id,
                'city': address_model.city.name,
                'district_id': address_model.district_id,
                'district': address_model.district.name,
                'place': address_model.place,
                'mobile': address_model.mobile,
                'tel': address_model.tel,
                'email': address_model.email
            })

        # 获取到用户默认收货地址的id
        default_address_id = user.default_address_id

        # 包装要传入模型的渲染数据
        context = {
            'addresses': addresses_list,
            'default_address_id': default_address_id
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(mixins.LoginRequiredMixin, View):
    """新增收获地址"""

    def post(self, request):

        # 判断用户当前收货地址的数量,不能超过20
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        # count = request.user.addresses.filter(is_deleted=False).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '收货地址数量超过上限'})

        # 接收请求体 body数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 新增收货地址
        address_model = Address.objects.create(
            user=request.user,
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        # 如果当前用户还没有默认收货地址,就把当前新增的收货地址直接设置为它的默认地址
        if request.user.default_address is None:
            request.user.default_address = address_model
            request.user.save()

        # 把新增的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加收货地址成功', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """收货地址修改和删除"""

    def put(self, request, address_id):

        # 接收请求体 body数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 查询出要修改的模型对象
        try:
            address_model = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # Address.objects.filter(id=address_id).update(
        address_model.title = title
        address_model.receiver = receiver
        address_model.province_id = province_id
        address_model.city_id = city_id
        address_model.district_id = district_id
        address_model.place = place
        address_model.mobile = mobile
        address_model.tel = tel
        address_model.email = email
        address_model.save()
        # )
        # 使用update去修改数据时,auto_now 不会重新赋值
        # 是调用save做的修改数据,会对auto_now 进行重新赋值

        # 把修改后的的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改收货地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除收货地址"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # 逻辑删除
        address.is_deleted = True
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class UpdateAddressTitleView(LoginRequiredView):
    """修改收货地址标题"""

    def put(self, request, address_id):

        # 接收前端传入的新标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        # 查询指定id的收货地址,并校验
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # 重新给收货地址模型的title属性赋值
        address.title = title
        address.save()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DefaultAddressView(LoginRequiredView):
    """设置用户默认收货地址"""

    def put(self, request, address_id):

        # 查询指定id的收货地址,并校验
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        # 获取当前user模型对象
        user = request.user

        # 给user的default_address 重新赋值
        user.default_address = address
        user.save()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class ChangePasswordView(LoginRequiredView):
    """修改用户密码"""

    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """修改密码逻辑"""
        # 接收请求中的表单数据
        query_dict = request.POST
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')

        # 校验
        if all([old_pwd, new_pwd, new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        user = request.user
        if user.check_password(old_pwd) is False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改用户密码
        user.set_password(new_pwd)
        user.save()

        return redirect('/logout/')


class UserBrowseHistory(LoginRequiredView):
    """
    用户浏览记录
    只记录登录用户的
    """

    def post(self, request):
        # 获取数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验数据
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id无效')

        user_id = request.user.id

        # 使用管道提供性能
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()

        # 去重
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 保存数据
        pl.lpush('history_%s' % user_id, sku_id)
        # 截取前5条记录，只保存5条记录
        pl.ltrim('history_%s' % user_id, 0, 4)
        pl.execute()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """
        展示浏览记录
        """
        redis_conn = get_redis_connection('history')
        sku_list = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        skus = []
        for sku in sku_list:
            sku = SKU.objects.get(id=sku)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class FindPasswd(View):
    """忘记密码跳转界面"""

    def get(self, request):
        return render(request, 'find_password.html')


class CheckUser(View):
    """忘记密码验证"""

    def get(self, request, username):
        # 接收前端过来的数据
        image_code_cli = request.GET.get('text')
        image_code_id = request.GET.get('image_code_id')  # 长字符串

        # 校验
        if all([username, image_code_cli, image_code_id]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5到20位用户名')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.JsonResponse({'error': '用户不存在'}, status=404)

        # 连接redis数据库
        redis_conn = get_redis_connection('verify_code')
        redis_image_code = redis_conn.get('img_%s' % image_code_id)  # 获取reids的验证码,bytes类型
        redis_conn.delete(image_code_id)  # 删除redis验证码,只能用一次
        redis_image_code_server = redis_image_code.decode()  # 将bytes转str

        # 判断验证码是否过期
        if redis_image_code is None:
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '图形验证码失效'})

        # 前后端验证码校验,大小写统一
        if image_code_cli.lower() != redis_image_code_server.lower():
            return http.JsonResponse({'error': '验证码不一致'}, status=400)

        # 获取当前用户手机号
        mobile = user.mobile
        data = {
            'username': username,
            'mobile': mobile
        }

        # 用户数据加密
        access_token = base64.b64encode(pickle.dumps(data)).decode()
        return http.JsonResponse(
            {'code': RETCODE.OK, 'errmsg': 'OK', 'mobile': str(mobile).replace(mobile[3:7], '*' * 4),
             'access_token': access_token})


class FindBackPw(View):
    """找回密码"""

    def get(self, request):
        # 接收加密数据
        access_token = request.GET.get('access_token')

        # 校验数据
        if access_token is None:
            return http.JsonResponse({'error': '用户或手机号错误'}, status=400)

        data = pickle.loads(base64.b64decode(access_token.encode()))
        mobile = data['mobile']

        redis_conn = get_redis_connection('verify_code')
        # 查询发送短信标记，如果60秒内发送过则提示过于频繁
        # send_flag = redis_conn.get('send_flag_%s' % mobile)
        # if send_flag:
        #     return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # 随机生成一个6位数字作为验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        # 管道发送验证码
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('send_flag_%s' % mobile, 300, 1)
        pl.execute()
        # 给当前手机号发短信,使用异步celery发送
        send_sms_code.delay(mobile, sms_code)
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信验证码成功'})


class VerifySmsCodeView(View):
    """验证短信验证码"""

    def get(self, request, username):
        sms_code = request.GET.get('sms_code')
        if sms_code is None:
            return http.JsonResponse({'code': 400})
        user = User.objects.get(username=username)
        mobile = user.mobile

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        sms_code_server = sms_code_server.decode()
        redis_conn.delete('sms_%s' % mobile)

        if not sms_code_server:
            return http.HttpResponseForbidden('验证码过期')

        if sms_code != sms_code_server:
            return http.JsonResponse({'code': RETCODE.SMSCODERR, 'errmsg': '验证码错误'}, status=400)
        data = {
            'user_id': user.id,
            'mobile': mobile
        }
        access_token = base64.b64encode(pickle.dumps(data)).decode()
        redis_conn.setex('access_token_sms_%s' % user.id, 300, access_token)  # 保存验证码

        return http.JsonResponse({'code': RETCODE.OK, 'user_id': user.id, 'access_token': access_token})


class ResetPasswd(View):
    """重置密码"""

    def post(self, request, user_id):
        # 接收数据
        json_dict = json.loads(request.body.decode())
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        access_token = json_dict.get('access_token')

        # 校验
        if all([password, password2, access_token]) is False:
            return http.HttpResponseForbidden("缺少必传参数")
        if not re.match(r'^[0-9a-zA-Z]{8,20}', password):
            return HttpResponseForbidden('请输入8到20位密码')
        if password != password2:
            return HttpResponseForbidden('两次输入密码不一致')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return http.HttpResponseForbidden('用户不存在')

        redis_conn = get_redis_connection('verify_code')
        access_token_server = redis_conn.get('access_token_sms_%s' % user.id)

        if access_token_server is None:
            return http.JsonResponse({'error': '数据错误'}, status=400)

        data = pickle.loads(base64.b64decode(access_token.encode()))
        if data is None:
            return http.JsonResponse({'error': '数据错误'}, status=400)

        user_id_server = data['user_id']

        if int(user_id) != user_id_server:
            return http.JsonResponse({'error': '数据错误'}, status=400)

        user.set_password(password)
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', })


class OrderInfoView(LoginRequiredView):
    """展示用户订单"""

    def get(self, request, current):

        # 1、查询当前用户的所有订单返回
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 如果没有订单则直接return
        if not orders:
            return render(request, 'user_center_order.html')
        # 创建分页器，每页展示3条订单数据
        paginator = Paginator(orders, 3)
        # 获取它的总页数
        total_page = paginator.num_pages
        # 获取当前页数
        page_num = current
        try:
            # 获取当前页面订单数据
            page_orders = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseNotFound('页面不存在')

        for order in orders:
            # 取出每个订单中的商品模型集
            ordergoods_list = order.skus.all()
            sku_list = []
            # 取出商品模型集中的每个商品模型
            for ordergood in ordergoods_list:
                sku = ordergood.sku
                sku.count = ordergood.count
                sku.amount = sku.price * sku.count
                sku_list.append(sku)
            # 给order新添加属性
            order.sku_list = sku_list
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method - 1][1]
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status - 1][1]
        context = {
            'page_orders': page_orders,
            'page_num': page_num,
            'total_page': total_page
        }

        return render(request, 'user_center_order.html', context)


class OrderComment(LoginRequiredView):
    """用户评价"""

    def get(self, request):
        # 先接收order_id
        order_id = request.GET.get('order_id')
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('无效订单')
        # 取出当前订单中未评价的所有商品
        ordergoods = order.skus.filter(comment='')
        # 创建前端需要的数据列表
        uncomment_goods_list = []
        for ordergood in ordergoods:
            uncomment_goods_list.append({
                'order_id': order_id,
                'sku_id': ordergood.sku.id,
                'name': ordergood.sku.name,
                'price': str(ordergood.sku.price),
                'default_image_url': ordergood.sku.default_image.url,
            })

        context = {
            'uncomment_goods_list': uncomment_goods_list
        }
        return render(request, 'goods_judge.html', context)

    def post(self, request):
        """获取用户评价"""
        # order_id: sku.order_id,
        # sku_id: sku.sku_id,
        # comment: sku.comment,
        # score: sku.final_score,
        # is_anonymous: sku.is_anonymous,
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        comment = json_dict.get('comment')
        score = json_dict.get('score')
        user = request.user
        is_anonymous = json_dict.get('is_anonymous')
        # 校验数据
        if all([order_id, sku_id, comment, score]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            orderinfo = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数order_id有误')
        try:
            ordergood = OrderGoods.objects.get(order_id=order_id, sku_id=sku_id)
        except OrderGoods.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id有误')
        if len(comment) < 5:
            return http.HttpResponseForbidden('评论字数不足')
        # 查询到ordergoods对象，update相关信息
        try:
            orderinfo.skus.filter(sku_id=sku_id).update(comment=comment, score=score, is_anonymous=is_anonymous,
                                                        is_commented=True)
            orderinfo.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
            orderinfo.save()
            print('ha')
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '评价成功'})
        except Exception:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '评价失败'})
