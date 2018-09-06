# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 10:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocteams', '0004_auto_20170929_1102'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jobjenkins',
            options={'ordering': ['jenkins_server', 'name']},
        ),
        migrations.AddField(
            model_name='jobjenkins',
            name='jenkins_server',
            field=models.CharField(default='Jenkins1', max_length=10),
            preserve_default=False,
        ),
    ]
