# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-03 09:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocteams', '0005_auto_20170929_1203'),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchGit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='repositorygit',
            name='branch_git',
            field=models.ManyToManyField(to='vocteams.BranchGit'),
        ),
    ]