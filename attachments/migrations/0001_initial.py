# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone

import attachments.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_path', models.TextField(unique=True)),
                ('file_name', models.CharField(max_length=200)),
                ('file_size', models.IntegerField()),
                ('context', models.CharField(db_index=True, max_length=200, blank=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('data', attachments.utils.JSONField(null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='attachments', to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=32)),
                ('template', models.CharField(default=b'attachments/list.html', max_length=200)),
                ('context', models.CharField(max_length=200, blank=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('user', models.ForeignKey(related_name='attachment_sessions', to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_path', models.TextField(unique=True)),
                ('file_name', models.CharField(max_length=200)),
                ('file_size', models.IntegerField()),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('session', models.ForeignKey(related_name='uploads', to='attachments.Session', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
