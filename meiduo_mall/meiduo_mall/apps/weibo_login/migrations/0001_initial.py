# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-09 09:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OAuthWeiBoUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('openid', models.CharField(db_index=True, max_length=64, verbose_name='openid')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='微博登录用户')),
            ],
            options={
                'verbose_name': '微博用户数据表',
                'verbose_name_plural': '微博用户数据表',
                'db_table': 'tb_oauth_weibo',
            },
        ),
    ]
