# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-24 14:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_auto_20180124_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationversionhistory',
            name='action',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='artifactversionhistory',
            name='action',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='applicationversionhistory',
            name='state_application_version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.StateApplicationVersion'),
        ),
        migrations.AlterField(
            model_name='artifactversionhistory',
            name='state_artifact_version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.StateArtifactVersion'),
        ),
    ]
