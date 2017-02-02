# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0010_property_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='model',
            field=models.CharField(help_text=b'The path to the lookup model for this field.', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='data_type',
            field=models.CharField(max_length=20, choices=[(b'string', b'Text'), (b'text', b'Large Text'), (b'integer', b'Integer'), (b'decimal', b'Decimal'), (b'boolean', b'Boolean'), (b'date', b'Date'), (b'email', b'Email Address'), (b'choice', b'Choice'), (b'model', b'Model')]),
        ),
    ]
