# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-10 13:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_environments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='environments',
            name='created',
        ),
    ]