# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0008_session_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='choices',
            field=models.TextField(help_text=b'Lookup choices for a ChoiceField, one per line.', blank=True),
        ),
        migrations.AddField(
            model_name='property',
            name='model',
            field=models.CharField(help_text=b'The path to the lookup model for a ModelChoiceField.', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='data_type',
            field=models.CharField(max_length=20, choices=[(b'string', b'Text'), (b'text', b'Large Text'), (b'integer', b'Integer'), (b'decimal', b'Decimal'), (b'boolean', b'Boolean'), (b'date', b'Date'), (b'email', b'Email Address'), (b'choice', b'Choice'), (b'model', b'Model')]),
        ),
    ]
