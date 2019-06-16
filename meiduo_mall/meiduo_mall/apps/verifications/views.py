from random import randint
from celery_tasks.sms.tasks import send_sms_code
from django import http
import logging
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from verifications import constants
from verifications.libs.captcha.captcha import captcha

logger = logging.getLogger('django')


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        # 接收图片验证码
        name, text, image = captcha.generate_captcha()

        # 保存图片验证码
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应图片验证码
        return http.HttpResponse(image, content_type='image/jpg')


# GET /sms_codes/15312345672/?image_code=5vib&uuid=99f6bc61-1f14-41eb-8f28-253258da20ee
class SMSCodeView(View):
    """发送短信验证码"""

    def get(self, request, mobile):

        # 来发短信之前先判断此手机号有没有在60s之前发过
        # 0. 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 尝试性去获取此手机号是否有发过短信的标记
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 如果胡提前响应
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '频繁发送短信'})

        # 1.接收前端传入的数据
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        # 2.校验数据
        if all([image_code_client, uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        # 2.2 获取redis中的图形验证码
        image_code_server = redis_conn.get("img_%s" % uuid)  # 从redis获取出来的数据都是bytes类型

        # 2.3 把redis中图形验证码删除
        redis_conn.delete(uuid)  # 只让图形验证码使用一次
        # 2.4 判断短信验证码是否过期
        if image_code_server is None:
            return http.HttpResponseForbidden('图形验证码过期')
        # 2.5 注册必须保证image_code_server它不会None再去调用decode
        print("aaa")
        image_code_server = image_code_server.decode()
        # 2. 6 判断用户输入验证码是否正确 注意转换大小写
        if image_code_client.lower() != image_code_server.lower():
            return http.HttpResponseForbidden('图形验证码输入有误')

        # 3. 随机生成一个6位数字作为验证码
        sms_code = '%06d' % randint(0, 999999)

        logger.info(sms_code)

        # redis管道技术
        pl = redis_conn.pipeline()
        # 将短信验证码存储到redis,以备后期注册时校验
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 向redis多存储一个此手机号已发送过短信的标记,此标记有效期60秒
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        # 执行管道
        pl.execute()

        # 给当前手机号发短信
        # CCP().send_template_sms(要收短信的手机号, [短信验证码, 短信中提示的过期时间单位分钟], 短信模板id)
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        send_sms_code.delay(mobile, sms_code)  # 生产任务
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信验证码成功'})
