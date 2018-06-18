# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=200)),
                ('slug', models.SlugField(help_text=b'Must be alphanumeric, with no spaces.', unique=True)),
                ('data_type', models.CharField(max_length=20, choices=[(b'string', b'Text'), (b'text', b'Large Text'), (b'integer', b'Integer'), (b'decimal', b'Decimal'), (b'boolean', b'Boolean'), (b'date', b'Date'), (b'lookup', b'Lookup (Dropdown)'), (b'radio', b'Lookup (Radio)'), (b'multi', b'Multi-Value Lookup (Checkboxes)'), (b'multilist', b'Multi-Value Lookup (Multi-Select)'), (b'email', b'Email Address')])),
                ('content_type', models.ManyToManyField(related_name='attachment_properties', to='contenttypes.ContentType', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
