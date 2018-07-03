# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_property'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='property',
            options={'verbose_name_plural': 'properties'},
        ),
    ]
