# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import attachments.utils


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0007_property_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='data',
            field=attachments.utils.JSONField(null=True),
        ),
    ]
