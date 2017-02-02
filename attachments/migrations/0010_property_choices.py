# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0009_auto_20170201_1323'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='choices',
            field=models.TextField(help_text=b'Lookup choices for this field, one per line.', blank=True),
        ),
    ]
