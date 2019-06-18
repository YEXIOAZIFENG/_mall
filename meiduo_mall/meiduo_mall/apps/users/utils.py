from django.contrib.auth.backends import ModelBackend
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
import re

from .models import User
from django.conf import settings


def get_user_by_account(account):
    """
    根据account查询用户
    :param account: 用户名或者手机号
    :return: user
    """
    try:
        if re.match('^1[3-9]\d{9}$', account):
            # 手机号登录
            user = User.objects.get(mobile=account)
        else:
            # 用户名登录
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法，实现多账号登录
        :param request: 请求对象
        :param username: 用户名
        :param password: 密码
        :param kwargs: 其他参数
        :return: user
        """
        # 根据传入的username获取user对象。username可以是手机号也可以是账号
        user = get_user_by_account(username)
        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user


def generate_verify_email_url(user):
    """拼接用户邮箱激活url"""

    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60 * 60 * 24)
    # 包装要加密的字典数据
    data = {'user_id': user.id, 'email': user.email}
    # 对字典进行加密
    token = serializer.dumps(data).decode()
    # 拼接用户激活邮箱url
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token

    return verify_url


def check_verify_email_token(token):
    """对token进行解密并返回user或None"""

    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60 * 60 * 24)
    try:
        data = serializer.loads(token)  # 解密
        user_id = data.get('user_id')  # 解密没有问题后取出里面数据
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)  # 查询唯一用户
            return user  # 查询到直接返回
        except User.DoesNotExist:
            return None

    except BadData:
        return None
