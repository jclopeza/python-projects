# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-23 07:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_auto_20170816_0655'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArtifactVersionHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('artifact_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.ArtifactVersion')),
                ('state_artifact_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.StateArtifactVersion')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.AlterModelOptions(
            name='artifactversionchangelog',
            options={'ordering': ['-created']},
        ),
    ]
