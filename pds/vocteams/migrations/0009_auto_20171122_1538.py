# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-22 14:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocteams', '0008_auto_20171019_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repositorygit',
            name='project_key',
            field=models.CharField(max_length=50),
        ),
    ]