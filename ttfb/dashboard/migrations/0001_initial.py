# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-13 08:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TTFB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=200)),
                ('ip', models.CharField(max_length=20)),
                ('dns_time', models.DecimalField(decimal_places=6, max_digits=20)),
                ('connection_time', models.DecimalField(decimal_places=6, max_digits=20)),
                ('time_to_first_byte', models.DecimalField(decimal_places=6, max_digits=20)),
                ('total_time', models.DecimalField(decimal_places=6, max_digits=20)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]