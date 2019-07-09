from django.db import models
from meiduo_mall.utils.models import BaseModel

# Create your models here.


class OAuthWeiBoUser(BaseModel):
    # 定义WeiBo登录用户模型类
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='微博登录用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_weibo'
        verbose_name = '微博用户数据表'
        verbose_name_plural = verbose_name