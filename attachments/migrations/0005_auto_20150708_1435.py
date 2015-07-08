# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0004_auto_20150507_1438'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='user',
            field=models.ForeignKey(related_name='attachments', blank=True, to='users.User', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='session',
            name='user',
            field=models.ForeignKey(related_name='attachment_sessions', blank=True, to='users.User', null=True),
            preserve_default=True,
        ),
    ]
