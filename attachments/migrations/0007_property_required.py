# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0006_session_content_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='required',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
