# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('attachments', '0005_auto_20150708_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
