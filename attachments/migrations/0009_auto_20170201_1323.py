# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0008_session_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='data_type',
            field=models.CharField(max_length=20, choices=[(b'string', b'Text'), (b'text', b'Large Text'), (b'integer', b'Integer'), (b'decimal', b'Decimal'), (b'boolean', b'Boolean'), (b'date', b'Date'), (b'email', b'Email Address'), (b'radio', b'Radio')]),
        ),
    ]
