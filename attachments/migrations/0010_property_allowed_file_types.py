# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-29 17:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0009_auto_20170202_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='allowed_file_types',
            field=models.CharField(blank=True, help_text='Space separated file types that are allowed for upload.', max_length=200),
        ),
    ]
