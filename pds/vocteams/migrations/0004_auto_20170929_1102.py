# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 09:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vocteams', '0003_auto_20170929_1100'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobjenkins',
            name='created',
        ),
        migrations.RemoveField(
            model_name='repositorygit',
            name='created',
        ),
    ]
